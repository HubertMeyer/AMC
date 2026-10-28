const GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token";
const MAX_REQUEST_BYTES = 16 * 1024;
const CLIENT_ID_PATTERN = /^[^\s\x00-\x1f]{20,512}\.apps\.googleusercontent\.com$/;
const PKCE_VERIFIER_PATTERN = /^[A-Za-z0-9._~-]{43,128}$/;

function jsonResponse(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      pragma: "no-cache",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
    },
  });
}

function configured(env) {
  return CLIENT_ID_PATTERN.test(String(env.GOOGLE_OAUTH_CLIENT_ID ?? ""))
    && typeof env.GOOGLE_OAUTH_CLIENT_SECRET === "string"
    && env.GOOGLE_OAUTH_CLIENT_SECRET.length >= 8
    && env.OAUTH_RATE_LIMITER
    && typeof env.OAUTH_RATE_LIMITER.limit === "function";
}

function validRedirect(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:"
      && url.hostname === "127.0.0.1"
      && url.port !== ""
      && url.username === ""
      && url.password === ""
      && url.pathname === "/youtube/callback/"
      && url.search === ""
      && url.hash === "";
  } catch {
    return false;
  }
}

function one(form, name, maxLength) {
  const values = form.getAll(name);
  if (values.length !== 1) return null;
  const value = values[0];
  return value && value.length <= maxLength ? value : null;
}

function parseTokenRequest(raw, env) {
  const form = new URLSearchParams(raw);
  const allowed = new Set([
    "client_id", "code", "code_verifier", "grant_type", "redirect_uri", "refresh_token",
  ]);
  if ([...form.keys()].some((name) => !allowed.has(name))) return null;
  const clientId = one(form, "client_id", 512);
  const grantType = one(form, "grant_type", 64);
  if (clientId !== env.GOOGLE_OAUTH_CLIENT_ID) return null;

  if (grantType === "authorization_code") {
    const code = one(form, "code", 4096);
    const verifier = one(form, "code_verifier", 128);
    const redirectUri = one(form, "redirect_uri", 512);
    if (!code || !verifier || !PKCE_VERIFIER_PATTERN.test(verifier)
      || !redirectUri || !validRedirect(redirectUri)
      || form.has("refresh_token")) return null;
    return new URLSearchParams({
      client_id: clientId,
      client_secret: env.GOOGLE_OAUTH_CLIENT_SECRET,
      code,
      code_verifier: verifier,
      grant_type: grantType,
      redirect_uri: redirectUri,
    });
  }

  if (grantType === "refresh_token") {
    const refreshToken = one(form, "refresh_token", 8192);
    if (!refreshToken || form.has("code") || form.has("code_verifier") || form.has("redirect_uri")) {
      return null;
    }
    return new URLSearchParams({
      client_id: clientId,
      client_secret: env.GOOGLE_OAUTH_CLIENT_SECRET,
      refresh_token: refreshToken,
      grant_type: grantType,
    });
  }
  return null;
}

function safeGooglePayload(text, success) {
  let source;
  try {
    source = JSON.parse(text);
  } catch {
    return null;
  }
  if (!source || typeof source !== "object" || Array.isArray(source)) return null;
  if (!success) {
    const error = typeof source.error === "string" ? source.error.slice(0, 100) : "server_error";
    return { error };
  }
  if (typeof source.access_token !== "string" || !source.access_token) return null;
  const result = {
    access_token: source.access_token,
    expires_in: Number.isInteger(source.expires_in) ? source.expires_in : 3600,
    token_type: typeof source.token_type === "string" ? source.token_type : "Bearer",
  };
  if (typeof source.refresh_token === "string" && source.refresh_token) {
    result.refresh_token = source.refresh_token;
  }
  if (typeof source.scope === "string" && source.scope) result.scope = source.scope;
  return result;
}

export function createWorker({ fetchImpl = fetch } = {}) {
  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (url.pathname === "/health" && request.method === "GET") {
        return configured(env)
          ? jsonResponse(200, { status: "ok", schemaVersion: 1 })
          : jsonResponse(503, { error: "service_unavailable" });
      }
      if (url.pathname !== "/v1/google/token") return jsonResponse(404, { error: "not_found" });
      if (request.method !== "POST") return jsonResponse(405, { error: "method_not_allowed" });
      if (!String(request.headers.get("content-type") ?? "").toLowerCase()
        .startsWith("application/x-www-form-urlencoded")) {
        return jsonResponse(415, { error: "invalid_request" });
      }
      if (!configured(env)) return jsonResponse(503, { error: "service_unavailable" });
      const declaredLength = Number(request.headers.get("content-length") ?? 0);
      if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { error: "invalid_request" });
      }
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { error: "invalid_request" });
      }
      const outgoing = parseTokenRequest(raw, env);
      if (!outgoing) return jsonResponse(400, { error: "invalid_request" });

      const clientAddress = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const limit = await env.OAUTH_RATE_LIMITER.limit({ key: `oauth:${clientAddress}` });
        if (!limit.success) return jsonResponse(429, { error: "rate_limited" });
      } catch {
        return jsonResponse(503, { error: "service_unavailable" });
      }

      let googleResponse;
      try {
        googleResponse = await fetchImpl(GOOGLE_TOKEN_ENDPOINT, {
          method: "POST",
          headers: { "content-type": "application/x-www-form-urlencoded" },
          body: outgoing.toString(),
        });
      } catch {
        return jsonResponse(502, { error: "server_error" });
      }
      const safe = safeGooglePayload(await googleResponse.text(), googleResponse.ok);
      if (!safe) return jsonResponse(502, { error: "server_error" });
      const status = googleResponse.ok
        ? 200
        : (googleResponse.status === 400 || googleResponse.status === 401 ? googleResponse.status : 502);
      return jsonResponse(status, safe);
    },
  };
}

export default createWorker();
