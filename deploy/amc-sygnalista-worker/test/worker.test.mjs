import assert from "node:assert/strict";
import test from "node:test";

import { createWorker, redactPrivateData } from "../src/worker.mjs";

class MemoryKv {
  constructor() { this.values = new Map(); }
  async get(key, type) {
    const value = this.values.get(key);
    if (value === undefined) return null;
    return type === "json" ? JSON.parse(value) : value;
  }
  async put(key, value) { this.values.set(key, value); }
}

function environment() {
  return {
    GITHUB_TOKEN: "worker-secret-never-returned",
    GITHUB_OWNER: "michalkasperczak",
    PUBLIC_REPOSITORY: "AMC",
    INTAKE_REPOSITORY: "amc-support-intake",
    REPORT_RESULTS: new MemoryKv(),
    REPORT_RATE_LIMITER: { limit: async () => ({ success: true }) },
  };
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
  const response = await createWorker().fetch(
    new Request("https://reports.example.test/health"),
    {},
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { status: "ok", schemaVersion: 1 });
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
  const env = environment();
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    const number = calls.length === 1 ? 12 : 34;
    return new Response(JSON.stringify({ number, html_url: `https://github.com/example/repo/issues/${number}` }), {
      status: 201,
      headers: { "content-type": "application/json" },
    });
  };
  const worker = createWorker({ fetchImpl });
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
  assert.doesNotMatch(JSON.stringify(firstBody).toLowerCase(), /worker-secret/);

  const duplicate = await worker.fetch(reportRequest(), env);
  assert.equal(duplicate.status, 201);
  assert.equal((await duplicate.json()).duplicate, true);
  assert.equal(calls.length, 2);
});

test("same id with different content is rejected", async () => {
  const env = environment();
  const fetchImpl = async (_url, _options) => new Response(
    JSON.stringify({ number: 1, html_url: "https://github.com/example/repo/issues/1" }),
    { status: 201 },
  );
  const worker = createWorker({ fetchImpl });
  assert.equal((await worker.fetch(reportRequest(), env)).status, 201);
  assert.equal((await worker.fetch(reportRequest(payload({ title: "Inny tytuł" })), env)).status, 409);
});

test("retry after public failure reuses the already created private report", async () => {
  const env = environment();
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
  const worker = createWorker({ fetchImpl });
  assert.equal((await worker.fetch(reportRequest(), env)).status, 502);
  assert.equal((await worker.fetch(reportRequest(), env)).status, 201);
  assert.equal(calls.filter((url) => url.includes("amc-support-intake")).length, 1);
  assert.equal(calls.filter((url) => url.includes("/AMC/issues")).length, 2);
});

test("invalid requests, size and rate limit receive explicit status", async () => {
  const worker = createWorker();
  const env = environment();
  assert.equal((await worker.fetch(new Request("https://reports.example.test/other"), env)).status, 404);
  assert.equal((await worker.fetch(new Request("https://reports.example.test/v1/report"), env)).status, 405);
  assert.equal((await worker.fetch(reportRequest(payload({ schemaVersion: 9 })), env)).status, 400);
  assert.equal((await worker.fetch(reportRequest(payload({ reportId: "bad" })), env)).status, 400);
  assert.equal((await worker.fetch(reportRequest(payload({ reportText: "x".repeat(270001) })), env)).status, 400);
  env.REPORT_RATE_LIMITER = { limit: async () => ({ success: false }) };
  assert.equal((await worker.fetch(reportRequest(), env)).status, 429);
});

test("GitHub failure is generic and never exposes the token", async () => {
  const env = environment();
  const worker = createWorker({ fetchImpl: async () => new Response("forbidden", { status: 403 }) });
  const response = await worker.fetch(reportRequest(), env);
  assert.equal(response.status, 502);
  assert.doesNotMatch(await response.text(), /worker-secret|forbidden/);
});
