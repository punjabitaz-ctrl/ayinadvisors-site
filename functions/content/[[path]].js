/**
 * Keeps /content/* off the live site - Cloudflare Pages Function.
 *
 * Cloudflare serves the whole repository, and content/ holds the build inputs, including approved blog posts
 * that are scheduled for a later Tuesday (content/blog/<slug>.frag and their entry in content/blog.json). The
 * pages are built from these files; nobody needs to fetch them, so every address under /content/ answers 404.
 */
export function onRequest() {
  return new Response('Not found', {
    status: 404,
    headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' },
  });
}
