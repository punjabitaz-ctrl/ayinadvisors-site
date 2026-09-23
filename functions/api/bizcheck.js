/**
 * BizCheck intake — Cloudflare Pages Function.
 *
 * Verifies the Turnstile token server-side before forwarding the brief to
 * Formspree. Verification cannot live in the browser: a client-side check is
 * forgeable, and the Formspree endpoint would still be public in page source.
 *
 * Environment (Pages → Settings → Environment variables):
 *   TURNSTILE_SECRET     secret  — Turnstile widget secret
 *   TURNSTILE_HOSTNAMES  plain   — comma-separated allowlist, e.g. "ayinadvisors.com"
 *                                  never include localhost/127.0.0.1 in production
 *   FORMSPREE_ENDPOINT   secret  — https://formspree.io/f/xxxxxxxx
 */

const EXPECTED_ACTION = 'bizcheck';
const SITEVERIFY = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const MAX_TOKEN_LENGTH = 2048;
const MAX_FIELD_LENGTH = 5000;

const FORWARDED_FIELDS = [
  'name', 'company', 'email', 'hq', 'stage', 'industry', 'description',
  'focus_areas', '_subject',
];

function reject(status = 403, message = 'forbidden') {
  return Response.json({ ok: false, error: message }, { status });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  const expectedHostnames = new Set(
    (env.TURNSTILE_HOSTNAMES ?? '').split(',').map((h) => h.trim()).filter(Boolean),
  );

  // Fail closed when the environment is not configured, rather than forwarding
  // unverified submissions.
  if (!env.TURNSTILE_SECRET || !env.FORMSPREE_ENDPOINT || expectedHostnames.size === 0) {
    // TEMPORARY: reports which of the three names are bound, never their values.
    // The names are already public in this repo and the 500 already reveals the
    // endpoint is unconfigured, so this adds no meaningful disclosure. Remove
    // once the variables are confirmed bound.
    return Response.json({
      ok: false,
      error: 'not configured',
      bound: {
        TURNSTILE_SECRET: Boolean(env.TURNSTILE_SECRET),
        TURNSTILE_HOSTNAMES: Boolean(env.TURNSTILE_HOSTNAMES),
        FORMSPREE_ENDPOINT: Boolean(env.FORMSPREE_ENDPOINT),
      },
    }, { status: 500 });
  }

  let form;
  try {
    form = await request.formData();
  } catch {
    return reject(400, 'bad request');
  }

  const token = form.get('cf-turnstile-response');
  if (typeof token !== 'string' || token.length === 0 || token.length > MAX_TOKEN_LENGTH) {
    return reject();
  }

  let result;
  try {
    const res = await fetch(SITEVERIFY, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      signal: AbortSignal.timeout(10_000),
      body: new URLSearchParams({
        secret: env.TURNSTILE_SECRET,
        response: token,
        remoteip: request.headers.get('CF-Connecting-IP') ?? '',
      }),
    });
    if (!res.ok) throw new Error(`siteverify ${res.status}`);
    result = await res.json();
  } catch {
    return reject();
  }

  if (
    !result.success ||
    result.action !== EXPECTED_ACTION ||
    !expectedHostnames.has(result.hostname)
  ) {
    return reject();
  }

  // Rebuild the payload from known fields so the Turnstile token and any
  // unexpected extras a caller appended are never relayed onward.
  const payload = new FormData();
  for (const field of FORWARDED_FIELDS) {
    const value = form.get(field);
    if (typeof value === 'string' && value.trim()) {
      payload.append(field, value.slice(0, MAX_FIELD_LENGTH));
    }
  }

  for (const required of ['name', 'company', 'email', 'description']) {
    if (!payload.get(required)) return reject(400, 'missing required fields');
  }

  try {
    const res = await fetch(env.FORMSPREE_ENDPOINT, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(10_000),
      body: payload,
    });
    if (!res.ok) throw new Error(`formspree ${res.status}`);
  } catch {
    return Response.json({ ok: false, error: 'delivery failed' }, { status: 502 });
  }

  return Response.json({ ok: true });
}

// Only POST is handled; Pages answers every other method with 405 on its own.
// An onRequest catch-all must not be exported here — it would take the POST too.
