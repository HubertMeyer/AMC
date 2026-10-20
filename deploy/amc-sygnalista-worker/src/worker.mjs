const MAX_REQUEST_BYTES = 300 * 1024;
const RESULT_TTL_SECONDS = 60 * 60 * 24 * 90;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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
    .replace(/\b(?:authorization|proxy-authorization|cookie|set-cookie)\s*:\s*[^\r\n]*/gi, "[nagłówek poufny usunięty]")
    .replace(/\bbearer\s+[a-z0-9._~+/=-]+/gi, "Bearer [wartość usunięta]")
    .replace(/\beyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,}(?:\.[a-zA-Z0-9_-]{10,})?\b/g, "[token usunięty]")
    .replace(/(^|[^a-zA-Z0-9_-])[a-zA-Z0-9_-]{64,}(?=$|[^a-zA-Z0-9_-])/g, "$1[wartość poufna usunięta]");
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
  if (typeof payload.reportText !== "string" || !payload.reportText.trim() || payload.reportText.length > 270000) {
    return { error: "Nieprawidłowa treść raportu" };
  }
  if (typeof payload.includedLog !== "boolean") return { error: "Nieprawidłowa informacja o dzienniku" };
  return {
    value: {
      schemaVersion: 1,
      reportId: payload.reportId.toLowerCase(),
      kind: payload.kind,
      title: redactPrivateData(payload.title).slice(0, 240),
      reportText: redactPrivateData(payload.reportText),
      includedLog: payload.includedLog,
    },
  };
}

function requireConfiguration(env) {
  const values = [env.GITHUB_TOKEN, env.GITHUB_OWNER, env.PUBLIC_REPOSITORY, env.INTAKE_REPOSITORY];
  return values.every((value) => typeof value === "string" && value.trim());
}

async function githubIssue(env, repository, data, fetchImpl) {
  const url = `https://api.github.com/repos/${encodeURIComponent(env.GITHUB_OWNER)}/${encodeURIComponent(repository)}/issues`;
  const response = await fetchImpl(url, {
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
  if (!response.ok) throw new Error(`GitHub zwrócił status ${response.status}`);
  const result = await response.json();
  if (!Number.isInteger(result.number) || result.number <= 0 || typeof result.html_url !== "string") {
    throw new Error("GitHub zwrócił niepełną odpowiedź");
  }
  return { number: result.number, url: result.html_url };
}

async function readState(env, reportId) {
  try {
    return await env.REPORT_RESULTS.get(reportId, "json");
  } catch {
    return null;
  }
}

async function writeState(env, reportId, state) {
  await env.REPORT_RESULTS.put(reportId, JSON.stringify(state), {
    expirationTtl: RESULT_TTL_SECONDS,
  });
}

export function createWorker({ fetchImpl = fetch } = {}) {
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (url.pathname === "/health" && request.method === "GET") {
        return jsonResponse(200, { status: "ok", schemaVersion: 1 });
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
      if (!requireConfiguration(env) || !env.REPORT_RESULTS || !env.REPORT_RATE_LIMITER) {
        return jsonResponse(503, { error: "Serwer zgłoszeń nie jest skonfigurowany" });
      }
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { error: "Raport jest zbyt duży" });
      }
      const parsed = parsePayload(raw);
      if (parsed.error) return jsonResponse(400, { error: parsed.error });
      const report = parsed.value;
      const contentHash = await sha256(JSON.stringify(report));
      let state = await readState(env, report.reportId);
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
      const clientAddress = request.headers.get("cf-connecting-ip") || "unknown";
      const rate = await env.REPORT_RATE_LIMITER.limit({ key: clientAddress });
      if (!rate.success) return jsonResponse(429, { error: "Zbyt wiele zgłoszeń" });

      try {
        if (!state?.privateIssueNumber) {
          const privateIssue = await githubIssue(env, env.INTAKE_REPOSITORY, {
            title: `[AMC][${report.kind}] ${report.title}`.slice(0, 250),
            body: `${report.reportText}\n\n---\nIdentyfikator raportu: ${report.reportId}\n`,
            labels: [report.kind === "bug" ? "bug" : "enhancement", "from-app"],
          }, fetchImpl);
          state = {
            contentHash,
            privateIssueNumber: privateIssue.number,
            privateIssueUrl: privateIssue.url,
          };
          await writeState(env, report.reportId, state);
        }
        const publicIssue = await githubIssue(env, env.PUBLIC_REPOSITORY, {
          title: report.title.slice(0, 250),
          body: [
            "Zgłoszenie przesłane z formularza AMC.",
            "",
            `Rodzaj: ${report.kind === "bug" ? "błąd" : "sugestia"}`,
            `Log dołączony do prywatnego raportu: ${report.includedLog ? "tak" : "nie"}`,
            `Prywatny zapis dla opiekuna: ${env.GITHUB_OWNER}/${env.INTAKE_REPOSITORY}#${state.privateIssueNumber}`,
            `Identyfikator raportu: ${report.reportId}`,
          ].join("\n"),
          labels: [report.kind === "bug" ? "bug" : "enhancement", "from-app"],
        }, fetchImpl);
        state = {
          ...state,
          publicIssueNumber: publicIssue.number,
          publicIssueUrl: publicIssue.url,
        };
        await writeState(env, report.reportId, state);
        return jsonResponse(201, {
          issueNumber: publicIssue.number,
          issueUrl: publicIssue.url,
          reportId: report.reportId,
          duplicate: false,
        });
      } catch {
        return jsonResponse(502, { error: "Nie udało się utworzyć zgłoszenia" });
      }
    },
  };
}

export default createWorker();
