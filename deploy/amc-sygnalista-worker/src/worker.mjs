const MAX_REQUEST_BYTES = 96 * 1024;
const MAX_REPORT_TEXT_CHARACTERS = 60 * 1024;
const RESULT_TTL_SECONDS = 60 * 60 * 24 * 90;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const REPORT_CHANNELS = new Set(["test", "stable"]);

function jsonResponse(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

export function redactPrivateData(value) {
  return String(value ?? "")
    .replace(/\0/g, "")
    .replace(/\bfile:\/\/\/[^\s"<>]+/gi, "[ścieżka prywatna]")
    .replace(/(?:[a-z]:[\\/]|\\\\)[^\r\n\t"<>|]+/gi, "[ścieżka prywatna]")
    .replace(/\b(?:https?|rtsp|mms):\/\/[^\s"<>]+/gi, "[adres usunięty]")
    .replace(/\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}\b/gi, "[adres e-mail usunięty]")
    .replace(/\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b/gi, "[adres urządzenia usunięty]")
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "[adres sieciowy usunięty]")
    .replace(/\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi, "[identyfikator usunięty]")
    .replace(/\b(?:authorization|proxy-authorization|cookie|set-cookie)\s*:\s*[^\r\n]*/gi, "[nagłówek poufny usunięty]")
    .replace(/\bbearer\s+[a-z0-9._~+/=-]+/gi, "Bearer [wartość usunięta]")
    .replace(/\b(?:access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|api[_ -]?key|password|passwd|account(?:[_ -]?name)?|user(?:[_ -]?name)?)\s*[:=]\s*(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\r\n]*)/gi, "[wartość konta usunięta]")
    .replace(/\beyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,}(?:\.[a-zA-Z0-9_-]{10,})?\b/g, "[token usunięty]")
    .replace(/(^|[^a-zA-Z0-9_-])[a-zA-Z0-9_-]{64,}(?=$|[^a-zA-Z0-9_-])/g, "$1[wartość poufna usunięta]")
    .replace(/(^|[^\w.-])[^\s\\/:*?"<>|]{1,180}\.(?:mp3|m4a|aac|flac|wav|ogg|opus|wma|mp4|mkv|avi|mov|webm|m3u8?|pls|asx|xspf|json|db|sqlite|log|txt)(?![\w.-])/gi, "$1[nazwa pliku usunięta]");
}

async function sha256(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((part) => part.toString(16).padStart(2, "0")).join("");
}

function parsePayload(raw) {
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    return { error: "Nieprawidłowy dokument JSON" };
  }
  if (!payload || payload.schemaVersion !== 1) return { error: "Nieobsługiwana wersja raportu" };
  if (!UUID_PATTERN.test(String(payload.reportId ?? ""))) return { error: "Nieprawidłowy identyfikator raportu" };
  if (!new Set(["bug", "suggestion"]).has(payload.kind)) return { error: "Nieprawidłowy rodzaj zgłoszenia" };
  if (typeof payload.title !== "string" || !payload.title.trim() || payload.title.length > 240) {
    return { error: "Nieprawidłowy tytuł" };
  }
  if (
    typeof payload.reportText !== "string"
      || !payload.reportText.trim()
      || payload.reportText.length > MAX_REPORT_TEXT_CHARACTERS
  ) {
    return { error: "Nieprawidłowa treść raportu" };
  }
  if (typeof payload.includedLog !== "boolean") return { error: "Nieprawidłowa informacja o dzienniku" };
  if (!REPORT_CHANNELS.has(payload.channel)) return { error: "Nieprawidłowy kanał raportu" };
  return {
    value: {
      schemaVersion: 1,
      reportId: payload.reportId.toLowerCase(),
      kind: payload.kind,
      title: redactPrivateData(payload.title).slice(0, 240),
      reportText: redactPrivateData(payload.reportText),
      includedLog: payload.includedLog,
      channel: payload.channel,
    },
  };
}

function requireConfiguration(env) {
  const values = [
    env.GITHUB_TOKEN,
    env.GITHUB_OWNER,
    env.PUBLIC_REPOSITORY,
    env.INTAKE_REPOSITORY,
    env.EXPECTED_CHANNEL,
  ];
  return values.every((value) => typeof value === "string" && value.trim())
    && REPORT_CHANNELS.has(env.EXPECTED_CHANNEL);
}

function requireBindings(env) {
  return Boolean(
    env.REPORT_COORDINATORS
      && typeof env.REPORT_COORDINATORS.getByName === "function"
      && env.REPORT_RATE_LIMITER
      && typeof env.REPORT_RATE_LIMITER.limit === "function",
  );
}

class GitHubRequestError extends Error {
  constructor(message, safeToRetry) {
    super(message);
    this.safeToRetry = safeToRetry;
  }
}

async function githubIssue(env, repository, data, fetchImpl) {
  const url = `https://api.github.com/repos/${encodeURIComponent(env.GITHUB_OWNER)}/${encodeURIComponent(repository)}/issues`;
  let response;
  try {
    response = await fetchImpl(url, {
      method: "POST",
      headers: {
        accept: "application/vnd.github+json",
        authorization: `Bearer ${env.GITHUB_TOKEN}`,
        "content-type": "application/json; charset=utf-8",
        "user-agent": "AMC-Sygnalista-Worker/1",
        "x-github-api-version": "2022-11-28",
      },
      body: JSON.stringify(data),
    });
  } catch {
    // A transport failure can happen after GitHub accepted the issue. Retrying
    // automatically would therefore risk creating a duplicate.
    throw new GitHubRequestError("Nie udało się potwierdzić odpowiedzi GitHuba", false);
  }
  if (!response.ok) {
    throw new GitHubRequestError(`GitHub zwrócił status ${response.status}`, true);
  }
  const result = await response.json();
  if (!Number.isInteger(result.number) || result.number <= 0 || typeof result.html_url !== "string") {
    // A successful status with an invalid body is ambiguous: the issue may
    // already exist, so keep the durable in-progress marker.
    throw new GitHubRequestError("GitHub zwrócił niepełną odpowiedź", false);
  }
  return { number: result.number, url: result.html_url };
}

async function readState(storage) {
  return await storage.get("result");
}

async function writeState(storage, state, { final = false } = {}) {
  await storage.put("result", state);
  if (final) {
    await storage.setAlarm(Date.now() + (RESULT_TTL_SECONDS * 1000));
  }
}

function storageUnavailable() {
  return jsonResponse(503, { error: "Magazyn zgłoszeń jest niedostępny" });
}

function issueFailure() {
  return jsonResponse(502, { error: "Nie udało się utworzyć zgłoszenia" });
}

export class ReportCoordinator {
  constructor(state, env, { fetchImpl = fetch } = {}) {
    this.state = state;
    this.env = env;
    this.fetchImpl = fetchImpl;
    this.pending = Promise.resolve();
  }

  fetch(request) {
    // Requests for one reportId are deliberately serialized for the whole
    // operation, including the two external GitHub calls. Durable storage
    // protects the result across eviction; the queue closes the await gaps
    // inside one live object instance.
    const operation = this.pending.then(() => this.handleRequest(request));
    this.pending = operation.then(() => undefined, () => undefined);
    return operation;
  }

  async alarm() {
    const operation = this.pending.then(() => this.state.storage.deleteAll());
    this.pending = operation.then(() => undefined, () => undefined);
    return await operation;
  }

  async handleRequest(request) {
    const url = new URL(request.url);
    if (url.pathname === "/ready" && request.method === "GET") {
      try {
        await readState(this.state.storage);
        return new Response(null, { status: 204 });
      } catch {
        return storageUnavailable();
      }
    }
    if (url.pathname !== "/v1/report") return jsonResponse(404, { error: "Nie znaleziono" });
    if (request.method !== "POST") return jsonResponse(405, { error: "Dozwolone jest tylko POST" });
    if (!requireConfiguration(this.env) || !this.env.REPORT_RATE_LIMITER) {
      return jsonResponse(503, { error: "Serwer zgłoszeń nie jest skonfigurowany" });
    }

    const parsed = parsePayload(await request.text());
    if (parsed.error) return jsonResponse(400, { error: parsed.error });
    const report = parsed.value;
    if (report.channel !== this.env.EXPECTED_CHANNEL) {
      return jsonResponse(400, { error: "Raport należy do innego kanału wydania" });
    }
    const contentHash = await sha256(JSON.stringify(report));
    let state;
    try {
      state = await readState(this.state.storage);
    } catch {
      return storageUnavailable();
    }
    if (state && state.contentHash !== contentHash) {
      return jsonResponse(409, { error: "Identyfikator należy do innej treści" });
    }
    if (state?.publicIssueNumber && state?.publicIssueUrl) {
      return jsonResponse(201, {
        issueNumber: state.publicIssueNumber,
        issueUrl: state.publicIssueUrl,
        reportId: report.reportId,
        duplicate: true,
      });
    }
    if (state?.phase === "creating-private" || state?.phase === "creating-public") {
      return storageUnavailable();
    }

    const clientAddress = request.headers.get("x-amc-client-address") || "unknown";
    try {
      const [clientRate, globalRate] = await Promise.all([
        this.env.REPORT_RATE_LIMITER.limit({ key: `client:${clientAddress}` }),
        this.env.REPORT_RATE_LIMITER.limit({ key: "service:all-reports" }),
      ]);
      if (!clientRate.success || !globalRate.success) {
        return jsonResponse(429, { error: "Zbyt wiele zgłoszeń" });
      }
    } catch {
      return jsonResponse(503, { error: "Serwer zgłoszeń nie jest skonfigurowany" });
    }

    if (!state?.privateIssueNumber) {
      const beforePrivate = { contentHash, phase: "creating-private" };
      try {
        await writeState(this.state.storage, beforePrivate);
      } catch {
        return storageUnavailable();
      }

      let privateIssue;
      try {
        privateIssue = await githubIssue(this.env, this.env.INTAKE_REPOSITORY, {
          title: `[AMC][${report.channel}][${report.kind}] ${report.title}`.slice(0, 250),
          body: `${report.reportText}\n\n---\nIdentyfikator raportu: ${report.reportId}\n`,
          labels: [
            report.kind === "bug" ? "bug" : "enhancement",
            "from-app",
            `channel:${report.channel}`,
          ],
        }, this.fetchImpl);
      } catch (error) {
        if (error instanceof GitHubRequestError && error.safeToRetry) {
          try {
            await writeState(this.state.storage, { contentHash });
          } catch {
            return storageUnavailable();
          }
        }
        return issueFailure();
      }

      state = {
        contentHash,
        privateIssueNumber: privateIssue.number,
        privateIssueUrl: privateIssue.url,
      };
      try {
        await writeState(this.state.storage, state);
      } catch {
        // The durable marker remains at creating-private. A retry must stop
        // instead of creating a second private issue.
        return storageUnavailable();
      }
    }

    const beforePublic = { ...state, phase: "creating-public" };
    try {
      await writeState(this.state.storage, beforePublic);
    } catch {
      return storageUnavailable();
    }

    let publicIssue;
    try {
      publicIssue = await githubIssue(this.env, this.env.PUBLIC_REPOSITORY, {
        title: report.title.slice(0, 250),
        body: [
          "Zgłoszenie przesłane z formularza AMC.",
          "",
          `Rodzaj: ${report.kind === "bug" ? "błąd" : "sugestia"}`,
          `Kanał: ${report.channel}`,
          `Log dołączony do prywatnego raportu: ${report.includedLog ? "tak" : "nie"}`,
          `Prywatny zapis dla opiekuna: ${this.env.GITHUB_OWNER}/${this.env.INTAKE_REPOSITORY}#${state.privateIssueNumber}`,
          `Identyfikator raportu: ${report.reportId}`,
        ].join("\n"),
        labels: [
          report.kind === "bug" ? "bug" : "enhancement",
          "from-app",
          `channel:${report.channel}`,
        ],
      }, this.fetchImpl);
    } catch (error) {
      if (error instanceof GitHubRequestError && error.safeToRetry) {
        try {
          await writeState(this.state.storage, state);
        } catch {
          return storageUnavailable();
        }
      }
      return issueFailure();
    }

    const completed = {
      ...state,
      publicIssueNumber: publicIssue.number,
      publicIssueUrl: publicIssue.url,
    };
    try {
      await writeState(this.state.storage, completed, { final: true });
    } catch {
      // creating-public is already durable, so a retry cannot duplicate the
      // public issue even when the final result write fails.
      return storageUnavailable();
    }
    return jsonResponse(201, {
      issueNumber: publicIssue.number,
      issueUrl: publicIssue.url,
      reportId: report.reportId,
      duplicate: false,
    });
  }
}

async function readinessResponse(env) {
  if (!requireConfiguration(env) || !requireBindings(env)) {
    return jsonResponse(503, { error: "Serwer zgłoszeń nie jest skonfigurowany" });
  }
  try {
    const stub = env.REPORT_COORDINATORS.getByName("amc-sygnalista-readiness-v1");
    const response = await stub.fetch(new Request("https://internal.invalid/ready"));
    if (response.status !== 204) return storageUnavailable();
  } catch {
    return storageUnavailable();
  }
  return jsonResponse(200, { status: "ok", schemaVersion: 1 });
}

export function createWorker() {
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (url.pathname === "/health" && request.method === "GET") {
        return await readinessResponse(env);
      }
      if (url.pathname !== "/v1/report") return jsonResponse(404, { error: "Nie znaleziono" });
      if (request.method !== "POST") return jsonResponse(405, { error: "Dozwolone jest tylko POST" });
      if (!String(request.headers.get("content-type") ?? "").toLowerCase().startsWith("application/json")) {
        return jsonResponse(415, { error: "Wymagany jest JSON" });
      }
      const length = Number(request.headers.get("content-length") ?? 0);
      if (Number.isFinite(length) && length > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { error: "Raport jest zbyt duży" });
      }
      if (!requireConfiguration(env) || !requireBindings(env)) {
        return jsonResponse(503, { error: "Serwer zgłoszeń nie jest skonfigurowany" });
      }
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { error: "Raport jest zbyt duży" });
      }
      const parsed = parsePayload(raw);
      if (parsed.error) return jsonResponse(400, { error: parsed.error });
      const report = parsed.value;
      const clientAddress = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const stub = env.REPORT_COORDINATORS.getByName(report.reportId);
        return await stub.fetch(new Request("https://internal.invalid/v1/report", {
          method: "POST",
          headers: {
            "content-type": "application/json; charset=utf-8",
            "x-amc-client-address": clientAddress,
          },
          body: JSON.stringify(report),
        }));
      } catch {
        return storageUnavailable();
      }
    },
  };
}

export default createWorker();
