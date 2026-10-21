import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

import { createWorker, redactPrivateData, ReportCoordinator } from "../src/worker.mjs";

test("deployment config requires secret and uses workers.dev", () => {
  const config = JSON.parse(fs.readFileSync(
    new URL("../wrangler.jsonc.example", import.meta.url),
    "utf8",
  ));
  assert.equal(config.workers_dev, true);
  assert.deepEqual(config.secrets.required, ["GITHUB_TOKEN"]);
  assert.equal(config.ratelimits[0].name, "REPORT_RATE_LIMITER");
  assert.deepEqual(config.durable_objects.bindings, [{
    name: "REPORT_COORDINATORS",
    class_name: "ReportCoordinator",
  }]);
  assert.deepEqual(config.migrations, [{
    tag: "v1",
    new_sqlite_classes: ["ReportCoordinator"],
  }]);
});

class MemoryDurableStorage {
  constructor({ failGet = false, failPutAt = null } = {}) {
    this.values = new Map();
    this.failGet = failGet;
    this.failPutAt = failPutAt;
    this.putCount = 0;
    this.alarm = null;
  }

  async get(key) {
    if (this.failGet) throw new Error("storage read failed");
    return this.values.get(key);
  }

  async put(key, value) {
    this.putCount += 1;
    if (this.failPutAt === this.putCount) throw new Error("storage write failed");
    this.values.set(key, structuredClone(value));
  }

  async setAlarm(value) { this.alarm = value; }
  async deleteAll() { this.values.clear(); }
}

class MemoryDurableNamespace {
  constructor(env, { fetchImpl, storageFactory }) {
    this.env = env;
    this.fetchImpl = fetchImpl;
    this.storageFactory = storageFactory;
    this.instances = new Map();
  }

  getByName(name) {
    if (!this.instances.has(name)) {
      const state = { storage: this.storageFactory(name) };
      const coordinator = new ReportCoordinator(state, this.env, { fetchImpl: this.fetchImpl });
      this.instances.set(name, { coordinator, state });
    }
    const entry = this.instances.get(name);
    return { fetch: (request) => entry.coordinator.fetch(request) };
  }

  storageFor(name) {
    this.getByName(name);
    return this.instances.get(name).state.storage;
  }
}

function environment({
  fetchImpl = async () => { throw new Error("unexpected GitHub request"); },
  storageFactory = () => new MemoryDurableStorage(),
} = {}) {
  const env = {
    GITHUB_TOKEN: "worker-secret-never-returned",
    GITHUB_OWNER: "michalkasperczak",
    PUBLIC_REPOSITORY: "AMC",
    INTAKE_REPOSITORY: "amc-support-intake",
    REPORT_RATE_LIMITER: { limit: async () => ({ success: true }) },
  };
  env.REPORT_COORDINATORS = new MemoryDurableNamespace(env, { fetchImpl, storageFactory });
  return env;
}

function payload(overrides = {}) {
  return {
    schemaVersion: 1,
    reportId: "123e4567-e89b-42d3-a456-426614174000",
    kind: "bug",
    title: "[Błąd] Radio nie startuje",
    reportText: "Raport AMC\nOpis:\nRadio nie startuje\n",
    includedLog: false,
    ...overrides,
  };
}

function reportRequest(body = payload(), headers = {}) {
  return new Request("https://reports.example.test/v1/report", {
    method: "POST",
    headers: { "content-type": "application/json", "cf-connecting-ip": "192.0.2.1", ...headers },
    body: JSON.stringify(body),
  });
}

test("health is small and does not expose configuration", async () => {
  let githubCalls = 0;
  const env = environment({ fetchImpl: async () => { githubCalls += 1; } });
  const response = await createWorker().fetch(
    new Request("https://reports.example.test/health"),
    env,
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: "ok", schemaVersion: 1 });
  assert.equal(githubCalls, 0);

  const missing = await createWorker().fetch(
    new Request("https://reports.example.test/health"),
    {},
  );
  assert.equal(missing.status, 503);
});

test("server performs a second privacy redaction", () => {
  const safe = redactPrivateData(
    [
      "C:\\Users\\Jan\\sekret.mp3 https://private.test jan@example.test",
      "Authorization: Bearer sekret",
      "access_token=krótki-sekret",
      "accountName: Jan Kowalski",
      "123e4567-e89b-42d3-a456-426614174000 radio.mp3",
    ].join("\n"),
  );
  assert.doesNotMatch(
    safe,
    /Jan|Kowalski|private\.test|jan@example|Bearer sekret|krótki-sekret|123e4567|radio\.mp3/,
  );
  assert.match(safe, /usunięty|prywatna/);
});

test("valid report creates private intake and public issue exactly once", async () => {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    const number = calls.length === 1 ? 12 : 34;
    return new Response(JSON.stringify({ number, html_url: `https://github.com/example/repo/issues/${number}` }), {
      status: 201,
      headers: { "content-type": "application/json" },
    });
  };
  const env = environment({ fetchImpl });
  const worker = createWorker();
  const first = await worker.fetch(reportRequest(), env);
  assert.equal(first.status, 201);
  const firstBody = await first.json();
  assert.deepEqual(firstBody, {
    issueNumber: 34,
    issueUrl: "https://github.com/example/repo/issues/34",
    reportId: payload().reportId,
    duplicate: false,
  });
  assert.equal(calls.length, 2);
  assert.match(calls[0].url, /amc-support-intake\/issues$/);
  assert.match(calls[1].url, /AMC\/issues$/);
  assert.equal(calls[0].options.headers.authorization, "Bearer worker-secret-never-returned");
  const privateIssue = JSON.parse(calls[0].options.body);
  const publicIssue = JSON.parse(calls[1].options.body);
  assert.match(privateIssue.body, /Raport AMC/);
  assert.doesNotMatch(publicIssue.body, /Raport AMC|Radio nie startuje/);
  assert.match(publicIssue.body, /Prywatny zapis dla opiekuna/);
  assert.doesNotMatch(JSON.stringify(firstBody).toLowerCase(), /worker-secret/);

  const duplicate = await worker.fetch(reportRequest(), env);
  assert.equal(duplicate.status, 201);
  assert.equal((await duplicate.json()).duplicate, true);
  assert.equal(calls.length, 2);
});

test("same id with different content is rejected", async () => {
  const fetchImpl = async (_url, _options) => new Response(
    JSON.stringify({ number: 1, html_url: "https://github.com/example/repo/issues/1" }),
    { status: 201 },
  );
  const env = environment({ fetchImpl });
  const worker = createWorker();
  assert.equal((await worker.fetch(reportRequest(), env)).status, 201);
  assert.equal((await worker.fetch(reportRequest(payload({ title: "Inny tytuł" })), env)).status, 409);
});

test("retry after public failure reuses the already created private report", async () => {
  const calls = [];
  const fetchImpl = async (url) => {
    calls.push(url);
    if (calls.length === 1) {
      return new Response(JSON.stringify({
        number: 12,
        html_url: "https://github.com/example/private/issues/12",
      }), { status: 201 });
    }
    if (calls.length === 2) return new Response("temporary", { status: 503 });
    return new Response(JSON.stringify({
      number: 34,
      html_url: "https://github.com/example/public/issues/34",
    }), { status: 201 });
  };
  const env = environment({ fetchImpl });
  const worker = createWorker();
  assert.equal((await worker.fetch(reportRequest(), env)).status, 502);
  assert.equal((await worker.fetch(reportRequest(), env)).status, 201);
  assert.equal(calls.filter((url) => url.includes("amc-support-intake")).length, 1);
  assert.equal(calls.filter((url) => url.includes("/AMC/issues")).length, 2);
});

test("parallel requests for one report id create each issue exactly once", async () => {
  const calls = [];
  let releaseFirstCall;
  let markFirstCallStarted;
  const firstCallStarted = new Promise((resolve) => { markFirstCallStarted = resolve; });
  const firstCallGate = new Promise((resolve) => { releaseFirstCall = resolve; });
  const fetchImpl = async (_url, _options) => {
    calls.push(_url);
    if (calls.length === 1) {
      markFirstCallStarted();
      await firstCallGate;
    }
    const number = calls.length === 1 ? 12 : 34;
    return new Response(JSON.stringify({
      number,
      html_url: `https://github.com/example/repo/issues/${number}`,
    }), { status: 201 });
  };
  const env = environment({ fetchImpl });
  const worker = createWorker();

  const firstPromise = worker.fetch(reportRequest(), env);
  await firstCallStarted;
  const secondPromise = worker.fetch(reportRequest(), env);
  releaseFirstCall();
  const [first, second] = await Promise.all([firstPromise, secondPromise]);
  const firstBody = await first.json();
  const secondBody = await second.json();

  assert.equal(first.status, 201);
  assert.equal(second.status, 201);
  assert.equal(firstBody.duplicate, false);
  assert.equal(secondBody.duplicate, true);
  assert.equal(calls.filter((url) => url.includes("amc-support-intake")).length, 1);
  assert.equal(calls.filter((url) => url.includes("/AMC/issues")).length, 1);
});

test("storage read and write failures stop before a duplicate side effect", async () => {
  let readFailureCalls = 0;
  const readFailureEnv = environment({
    fetchImpl: async () => { readFailureCalls += 1; },
    storageFactory: () => new MemoryDurableStorage({ failGet: true }),
  });
  const worker = createWorker();
  assert.equal((await worker.fetch(reportRequest(), readFailureEnv)).status, 503);
  assert.equal(readFailureCalls, 0);

  let initialWriteCalls = 0;
  const initialWriteFailureEnv = environment({
    fetchImpl: async () => { initialWriteCalls += 1; },
    storageFactory: () => new MemoryDurableStorage({ failPutAt: 1 }),
  });
  assert.equal((await worker.fetch(reportRequest(), initialWriteFailureEnv)).status, 503);
  assert.equal(initialWriteCalls, 0);

  let acceptedPrivateCalls = 0;
  const finalWriteFailureEnv = environment({
    fetchImpl: async () => {
      acceptedPrivateCalls += 1;
      return new Response(JSON.stringify({
        number: 12,
        html_url: "https://github.com/example/private/issues/12",
      }), { status: 201 });
    },
    // The first write persists creating-private. The second write fails after
    // GitHub accepted the private issue, leaving the durable guard in place.
    storageFactory: () => new MemoryDurableStorage({ failPutAt: 2 }),
  });
  assert.equal((await worker.fetch(reportRequest(), finalWriteFailureEnv)).status, 503);
  assert.equal((await worker.fetch(reportRequest(), finalWriteFailureEnv)).status, 503);
  assert.equal(acceptedPrivateCalls, 1);
});

test("invalid requests, size and rate limit receive explicit status", async () => {
  const worker = createWorker();
  const env = environment();
  assert.equal((await worker.fetch(new Request("https://reports.example.test/other"), env)).status, 404);
  assert.equal((await worker.fetch(new Request("https://reports.example.test/v1/report"), env)).status, 405);
  assert.equal((await worker.fetch(reportRequest(payload({ schemaVersion: 9 })), env)).status, 400);
  assert.equal((await worker.fetch(reportRequest(payload({ reportId: "bad" })), env)).status, 400);
  assert.equal((await worker.fetch(reportRequest(payload({ reportText: "x".repeat((60 * 1024) + 1) })), env)).status, 400);
  env.REPORT_RATE_LIMITER = { limit: async () => ({ success: false }) };
  assert.equal((await worker.fetch(reportRequest(), env)).status, 429);
});

test("accepted report consumes both client and global abuse limits", async () => {
  const keys = [];
  let issueNumber = 500;
  const env = environment({
    fetchImpl: async () => {
      issueNumber += 1;
      return new Response(JSON.stringify({
        number: issueNumber,
        html_url: `https://github.com/michalkasperczak/AMC/issues/${issueNumber}`,
      }), { status: 201 });
    },
  });
  env.REPORT_RATE_LIMITER = {
    limit: async ({ key }) => {
      keys.push(key);
      return { success: true };
    },
  };
  const request = reportRequest();
  request.headers.set("cf-connecting-ip", "203.0.113.24");

  assert.equal((await createWorker().fetch(request, env)).status, 201);
  assert.deepEqual(keys.sort(), ["client:203.0.113.24", "service:all-reports"]);
});

test("GitHub failure is generic and never exposes the token", async () => {
  const env = environment({ fetchImpl: async () => new Response("forbidden", { status: 403 }) });
  const worker = createWorker();
  const response = await worker.fetch(reportRequest(), env);
  assert.equal(response.status, 502);
  assert.doesNotMatch(await response.text(), /worker-secret|forbidden/);
});
