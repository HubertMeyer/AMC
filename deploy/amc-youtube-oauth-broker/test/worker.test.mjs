import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

import { createWorker } from "../src/worker.mjs";

const CLIENT_ID = "123456789012-example.apps.googleusercontent.com";
const CLIENT_SECRET = "server-secret-never-returned";
const VERIFIER = "v".repeat(43);

test("deployment config keeps the client secret outside the file", () => {
  const config = JSON.parse(fs.readFileSync(
    new URL("../wrangler.jsonc.example", import.meta.url),
    "utf8",
  ));
  assert.deepEqual(config.secrets.required, ["GOOGLE_OAUTH_CLIENT_SECRET"]);
  assert.equal(config.vars.GOOGLE_OAUTH_CLIENT_SECRET, undefined);
  assert.equal(config.ratelimits[0].name, "OAUTH_RATE_LIMITER");
  assert.equal(config.observability.logs.enabled, false);
});

function environment() {
  return {
    GOOGLE_OAUTH_CLIENT_ID: CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET: CLIENT_SECRET,
    OAUTH_RATE_LIMITER: { limit: async () => ({ success: true }) },
  };
}

function tokenRequest(fields, headers = {}) {
  return new Request("https://oauth.amc.example/v1/google/token", {
    method: "POST",
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      "cf-connecting-ip": "192.0.2.10",
      ...headers,
    },
    body: new URLSearchParams(fields),
  });
}

test("authorization code exchange injects the server secret and returns only token fields", async () => {
  let forwarded;
  const worker = createWorker({ fetchImpl: async (url, options) => {
    forwarded = { url, options };
    return new Response(JSON.stringify({
      access_token: "access",
      refresh_token: "refresh",
      expires_in: 3600,
      scope: "https://www.googleapis.com/auth/youtube.readonly",
      id_token: "identity-must-not-leave-broker",
    }), { status: 200 });
  } });
  const response = await worker.fetch(tokenRequest({
    client_id: CLIENT_ID,
    code: "one-time-code",
    code_verifier: VERIFIER,
    grant_type: "authorization_code",
    redirect_uri: "http://127.0.0.1:49321/youtube/callback/",
  }), environment());
  assert.equal(response.status, 200);
  assert.equal(forwarded.url, "https://oauth2.googleapis.com/token");
  const form = new URLSearchParams(forwarded.options.body);
  assert.equal(form.get("client_secret"), CLIENT_SECRET);
  assert.equal(form.get("code_verifier"), VERIFIER);
  const body = await response.json();
  assert.equal(body.refresh_token, "refresh");
  assert.equal(body.id_token, undefined);
  assert.doesNotMatch(JSON.stringify(body), /server-secret|identity-must/);
});

test("refresh is accepted without exposing secret or error description", async () => {
  const worker = createWorker({ fetchImpl: async (_url, options) => {
    assert.equal(new URLSearchParams(options.body).get("client_secret"), CLIENT_SECRET);
    return new Response(JSON.stringify({
      error: "invalid_grant",
      error_description: `private ${CLIENT_SECRET}`,
    }), { status: 400 });
  } });
  const response = await worker.fetch(tokenRequest({
    client_id: CLIENT_ID,
    refresh_token: "refresh",
    grant_type: "refresh_token",
  }), environment());
  assert.equal(response.status, 400);
  assert.deepEqual(await response.json(), { error: "invalid_grant" });
});

test("wrong client, unsafe callback, extra secret and invalid PKCE are rejected before Google", async () => {
  let calls = 0;
  const worker = createWorker({ fetchImpl: async () => { calls += 1; } });
  const base = {
    client_id: CLIENT_ID,
    code: "code",
    code_verifier: VERIFIER,
    grant_type: "authorization_code",
    redirect_uri: "http://127.0.0.1:49321/youtube/callback/",
  };
  for (const fields of [
    { ...base, client_id: "999999999999-other.apps.googleusercontent.com" },
    { ...base, redirect_uri: "http://localhost:49321/youtube/callback/" },
    { ...base, client_secret: "attacker-secret" },
    { ...base, code_verifier: "short" },
  ]) {
    assert.equal((await worker.fetch(tokenRequest(fields), environment())).status, 400);
  }
  assert.equal(calls, 0);
});

test("configuration, media type, size and rate limit fail closed", async () => {
  const worker = createWorker({ fetchImpl: async () => { throw new Error("unexpected"); } });
  assert.equal((await worker.fetch(
    new Request("https://oauth.amc.example/health"), environment(),
  )).status, 200);
  assert.equal((await worker.fetch(
    new Request("https://oauth.amc.example/health"), {},
  )).status, 503);
  assert.equal((await worker.fetch(tokenRequest({}), {})).status, 503);
  const wrongType = tokenRequest({});
  wrongType.headers.set("content-type", "application/json");
  assert.equal((await worker.fetch(wrongType, environment())).status, 415);
  const limited = environment();
  limited.OAUTH_RATE_LIMITER = { limit: async () => ({ success: false }) };
  assert.equal((await worker.fetch(tokenRequest({
    client_id: CLIENT_ID,
    refresh_token: "refresh",
    grant_type: "refresh_token",
  }), limited)).status, 429);
  const oversized = tokenRequest({});
  oversized.headers.set("content-length", String((16 * 1024) + 1));
  assert.equal((await worker.fetch(oversized, environment())).status, 413);
});
