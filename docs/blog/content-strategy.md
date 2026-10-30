# AYiN Advisors blog: content strategy

Draft for Taz's sign-off, October 28, 2026.

## The goal

Be the clearest answer to the questions AYiN's three kinds of buyer type into Google, ChatGPT, Perplexity and Google's AI answers. Every post answers one real question, links to the service that solves it, and sends readers to the contact form with that practice already picked.

The blog is linked from the footer only. Readers will mostly arrive on a post from a search, not from the menu, so each post has to stand on its own.

## Who we write for

| Practice | Buyer (from the site) | What they search for |
|---|---|---|
| B2B Partnerships | International firms entering the US | How to sell in the US, which channel, how to find and vet partners, what agreements cover |
| B2B Partnerships (channel strategy) | Vendors building or fixing a partner channel | What resellers need, onboarding, incentives, partner metrics |
| AI Solutions Development | Teams that need AI built | Where to start, build or buy, what drives cost, keeping people in the loop |
| Digital Presence | Businesses building their presence online | Why they are not on Google, how to show up in AI answers, what a site needs |

## How every post is written

1. **The question is the title.** Use the words a buyer would type, not a clever headline.
2. **Answer first.** The first section, "The short answer", answers in two to four sentences. This is the part Google and AI tools quote. (published)
3. **Then go deeper.** Each section heading is a follow-up question a reader would ask next. (published)
4. **One practice per post.** The post links two or three services of that practice, and its closing button opens the contact form with the practice picked.
5. **Only what we can stand behind.** No invented numbers, client results or quotes. When a fact needs a source, link a primary one (a government or official page). Where a topic touches law or tax, say it is general guidance and point to a qualified adviser.
6. **Signed and dated.** Every post carries Taz's byline and a published and updated date, and is marked up as a BlogPosting by the founder. (published)
7. **No em dashes**, plain words, short paragraphs, as on the rest of the site.

## Topic clusters and post titles

Titles marked "published" are live on the blog. The rest are proposals; each is drafted for Taz's review before it is published.

### A. Entering the US through partners (B2B Partnerships)

1. Distributor, reseller or agent: which US route to market fits your product? (published)
2. How do you find and vet a US distributor?
3. What should a US distribution agreement cover before you sign?
4. What decides how long it takes to get a first US partner selling?
5. Do you need a US company to start selling in the United States?
6. What does a US market entry study include, and is it worth it?
7. After the US: when should you expand into Canada or Latin America, and in what order?

### B. Building a partner channel that sells (B2B Partnerships, channel strategy)

8. What does a reseller need from a new vendor before they will sell it? (published)
9. How do you build a partner onboarding program that leads to a first deal? (published)
10. Rebates, MDF and deal registration: which partner incentives work?
11. Which partner program measures matter in the first year?

### C. Putting AI to work in a small team (AI Solutions Development)

12. Where should a small team start with workflow automation? (published)
13. Build or buy: when does a custom application make sense? (published)
14. What drives the cost of a custom AI tool? (published)
15. How do you keep a person in the loop in an automated workflow?
16. How do you stop an AI tool from making things up about your products?

### D. Being found online (Digital Presence)

17. Why isn't my new website showing up on Google? (published)
18. How does a business get mentioned in ChatGPT and Google's AI answers? (published)
19. What should a B2B website have before you start outreach?
20. Does a small B2B firm need a blog?

## Order and cadence

Updated October 29, 2026: Taz approved all nine drafts written for the weekly schedule and asked for them to go live at once, so eleven posts are live. New posts keep the 750-word minimum. The Tuesday 8am Eastern publishing (below) stays in place for future approved posts given a future date.

| Published | Post | Practice |
|---|---|---|
| Oct 28 | 1. Distributor, reseller or agent | B2B Partnerships |
| Oct 28 | 12. Where to start with workflow automation | AI Solutions Development |
| Oct 29 | 8. What a reseller needs from a new vendor | B2B Partnerships |
| Oct 29 | 17. Why a new website is not on Google | Digital Presence |
| Oct 29 | 2. How to find and vet a US distributor | B2B Partnerships |
| Oct 29 | 13. Build or buy a custom application | AI Solutions Development |
| Oct 29 | 3. What a US distribution agreement should cover | B2B Partnerships |
| Oct 29 | 18. How to get mentioned in AI answers | Digital Presence |
| Oct 29 | 9. Partner onboarding that leads to a first deal | B2B Partnerships |
| Oct 29 | 14. What drives the cost of a custom AI tool | AI Solutions Development |
| Oct 29 | 6. What a US market entry study includes | B2B Partnerships |

Still to draft: 4, 5, 7, 10, 11, 15, 16, 19 and 20.

## How we will know it works

- Google Search Console: impressions and clicks for each post, and the actual search queries that bring readers. This needs Search Console set up for ayinadvisors.com.
- Cloudflare Web Analytics: visits to each post and visits arriving from AI tools.
- Contact form: enquiries arriving with a practice picked from a post.

After three months, write more on the topics that draw impressions and drop or merge the ones that do not. Add new questions as they come up in real conversations with buyers.

## How the research was done

Topics come from what currently ranks for each practice's core questions on Google, and from how AI search tools and buyers phrase these questions in 2026. Search volumes were not measured: no keyword tool was reachable. Once Search Console has a few weeks of data, it will show which questions people actually ask.

## How a post gets published

1. Claude drafts the post outside this repository and shares it with Taz for review, in the Claude Doc "AYiN blog drafts for review".
2. Taz gives editorial feedback; Claude revises until Taz approves that exact draft.
3. Only then does the post go into the repository, through a pull request, with its Tuesday as its "published" date.
4. At 8am Eastern that Tuesday, the GitHub Action `.github/workflows/publish-scheduled-posts.yml` rebuilds the site, runs the tests and pushes the new page, the updated blog index and the new sitemap to master. Cloudflare Pages deploys the push.

Unapproved drafts never go into this repository. An approved post can wait here before its Tuesday: until then `build.py` gives it no page, no place on the index and no sitemap entry, and `/content/` answers 404 on the live site. The repository itself is public on GitHub, so a queued post can be read there before its date.

## How to add an approved post

1. Add the post to `content/blog.json` (slug, question, summary, practice, two or three related service pages). Set "published" and "updated" to its Tuesday.
2. Write the body in `content/blog/<slug>.frag`, starting with an `h2` "The short answer". At least 750 words.
3. Add the page to `content/site.json` as `blog/<slug>` with `"template": "post"`, a title under 60 characters ending " - AYiN Advisors", a 70 to 160 character description, its canonical address and a sitemap entry whose lastmod is its Tuesday.
4. Run the tests: `python -m pytest --ignore=tests/a11y_browser`. To preview the site as it will be that morning, set `AYIN_BUILD_NOW`, for example `AYIN_BUILD_NOW=2026-11-03T08:00 python build.py`, and do not commit the result.

A post dated today or earlier goes live on merge instead: run `python build.py` and `python tools/baseline.py snapshot` before committing.

## Telling Google

Google retired its sitemap "ping" in 2023. The sitemap is listed in `robots.txt`, and Google rereads it on its own schedule, using each page's lastmod. To submit it the moment a post goes live, the workflow can call the Search Console API. That needs, once:

1. Verify ayinadvisors.com in Google Search Console (a Domain property, through a DNS record in Cloudflare) and submit `https://ayinadvisors.com/sitemap.xml` there.
2. In Google Cloud, create a service account, enable the Search Console API, and make a JSON key.
3. In Search Console, add the service account's email as an Owner of the property.
4. In GitHub, add the JSON key as the Actions secret `GSC_SERVICE_ACCOUNT_JSON`. For a URL-prefix property instead of a Domain property, also add the Actions variable `GSC_SITE` set to `https://ayinadvisors.com/`.

Until the secret exists, the workflow skips this step and the posts still go live.
