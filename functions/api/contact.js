/**
 * Consultation request — Cloudflare Pages Function.
 *
 * Mirrors functions/api/bizcheck.js: verifies the Turnstile token server-side
 * before forwarding to Formspree, so the form endpoint stays out of page source
 * and a caller cannot POST straight past the browser-side checks.
 *
 * Shares TURNSTILE_SECRET and TURNSTILE_HOSTNAMES with the BizCheck surface —
 * one widget, one hostname allowlist. The action differs so the two surfaces
 * stay distinguishable at siteverify, and each has its own Formspree form.
 *
 * Environment (Pages → Settings → Environment variables → Production):
 *   TURNSTILE_SECRET            secret — Turnstile widget secret
 *   TURNSTILE_HOSTNAMES         plain  — e.g. "ayinadvisors.com", never localhost
 *   CONTACT_FORMSPREE_ENDPOINT  secret — https://formspree.io/f/xxxxxxxx
 */

const EXPECTED_ACTION = 'contact';
const SITEVERIFY = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
const MAX_TOKEN_LENGTH = 2048;
const MAX_FIELD_LENGTH = 5000;

const FORWARDED_FIELDS = ['name', 'company', 'email', 'hq', 'msg', 'interests', '_subject'];

function reject(status = 403, message = 'forbidden') {
  return Response.json({ ok: false, error: message }, { status });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  const expectedHostnames = new Set(
    (env.TURNSTILE_HOSTNAMES ?? '').split(',').map((h) => h.trim()).filter(Boolean),
  );

  if (!env.TURNSTILE_SECRET || !env.CONTACT_FORMSPREE_ENDPOINT || expectedHostnames.size === 0) {
    return reject(500, 'not configured');
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

  const payload = new FormData();
  for (const field of FORWARDED_FIELDS) {
    const value = form.get(field);
    if (typeof value === 'string' && value.trim()) {
      payload.append(field, value.slice(0, MAX_FIELD_LENGTH));
    }
  }

  for (const required of ['name', 'company', 'email']) {
    if (!payload.get(required)) return reject(400, 'missing required fields');
  }

  try {
    const res = await fetch(env.CONTACT_FORMSPREE_ENDPOINT, {
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
