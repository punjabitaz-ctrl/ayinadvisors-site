<h2 id="short-answer">The short answer</h2>
<p>A new website usually is not on Google yet because Google has not found it, has found it but not crawled it, or has crawled it and not yet decided to show it. None of these is a penalty. The fix is to make the site easy to discover and read: verify it in Google Search Console, submit the sitemap, make sure nothing is blocking Google, and give it a few links from places Google already visits. Then allow time.</p>

<h2 id="how-google-finds-pages">How Google finds a page</h2>
<p>Google works in three stages. It discovers a page, usually by following a link from another page or by reading a sitemap. It crawls the page, fetching its content. Then it indexes the page, deciding whether to store it and show it in results. A new site can be stuck at any of the three, and each has different causes.</p>
<p>A quick check is to search Google for <code>site:</code> followed by your domain, for example <code>site:example.com</code>. If nothing appears, Google has not indexed any pages yet. This check is rough, so use Search Console for an accurate picture.</p>

<h2 id="not-discovered">Google has not discovered it</h2>
<p>A brand-new domain has no links pointing to it, so Google has no path to it. This is the most common reason a site launched in the last few weeks does not appear.</p>
<ul>
  <li><strong>Verify the site in Google Search Console.</strong> This is free and shows you what Google knows about your site. Use the domain property if you can, since it covers every version of the address.</li>
  <li><strong>Submit your sitemap.</strong> A sitemap is a file listing your pages. Most site builders create one automatically. Submit its address in Search Console under Sitemaps, and list it in your robots.txt file as well.</li>
  <li><strong>Get a few real links.</strong> Your LinkedIn company page, your Google Business Profile, industry directories and partners' websites all give Google a path to you.</li>
</ul>
<p>Google used to accept a simple "ping" telling it a sitemap had changed. It retired that in 2023. Today the sitemap in Search Console and in robots.txt is how Google learns about updates, using the last-modified dates inside the sitemap.</p>

<h2 id="blocked">Something is blocking Google</h2>
<p>Sites often launch with a setting left over from development. Check these in order:</p>
<ol>
  <li><strong>robots.txt.</strong> Open your domain followed by <code>/robots.txt</code>. A line reading <code>Disallow: /</code> under <code>User-agent: *</code> tells every search engine to stay out.</li>
  <li><strong>A noindex tag.</strong> Many website platforms have a "hide from search engines" option for sites under construction. If it was left on, each page tells Google not to index it.</li>
  <li><strong>Password protection or a holding page.</strong> If visitors need a password, so does Google.</li>
  <li><strong>Firewall or bot protection.</strong> Aggressive security settings can block Googlebot along with bad bots. Your hosting or security provider can confirm whether Google's crawler is allowed.</li>
</ol>
<p>The URL Inspection tool in Search Console will tell you directly whether a page is blocked and why.</p>

<h2 id="crawled-not-indexed">Crawled but not indexed</h2>
<p>Search Console may report a page as "Discovered, currently not indexed" or "Crawled, currently not indexed." That means Google knows about the page but has not chosen to include it yet. On a new site this often resolves with time. If it persists, look at the page itself. Very short pages, near-duplicates of other pages, or pages that say little that is not said elsewhere are less likely to be indexed.</p>
<p>Also check canonical tags. Each page should point to its own preferred address. A template error that points every page to the home page tells Google to ignore the rest.</p>

<h2 id="indexed-not-ranking">Indexed but hard to find</h2>
<p>Sometimes the site is indexed but does not appear for the searches you try. Search your exact business name first. If you appear for that, the site is in Google, and the question becomes ranking, which takes content that answers what your buyers search for and links that show other sites trust you. A new site rarely ranks for broad, competitive phrases in its first months, and that is normal.</p>

<p>Bing deserves attention as well. It powers several other search services, and some AI search tools draw on its results, so verifying your site in Bing Webmaster Tools is worth the few minutes it takes.</p>

<h2 id="a-launch-checklist">A launch checklist</h2>
<ul>
  <li>Verify the site in Google Search Console and Bing Webmaster Tools.</li>
  <li>Submit the sitemap in both, and list it in robots.txt.</li>
  <li>Inspect the home page and a few key pages with URL Inspection and request indexing.</li>
  <li>Confirm robots.txt, noindex settings and security rules allow search crawlers.</li>
  <li>Give every page a unique title, description and canonical address.</li>
  <li>Link to the site from your business profiles and from partners.</li>
  <li>Check the Pages report in Search Console every week or two for the first couple of months.</li>
</ul>

<h2 id="how-long">How long should it take?</h2>
<p>There is no fixed timeline, and Google does not promise to index every page. A small, well-built site with a submitted sitemap and a few links is often picked up within days to a few weeks. Requesting indexing can help an important page, but asking repeatedly does not speed it up. If several weeks pass with nothing indexed, go back through the blocking checks above, because a setting is the usual cause.</p>
