# Survey Wellfound and YC Work at a Startup against the GET/JSON boundary

<!-- wayfinder:research -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

Do Wellfound (formerly AngelList Talent) and Y Combinator's Work at a Startup expose UK
graduate and entry-level engineering roles through an unauthenticated HTTP **GET** whose
response is JSON — and if not, what is the highest-ROI way to reach the companies they
list?

These were named as high-ROI startup sources. This project already has a settled test for
exactly this judgement:
[the ATS platform survey](../../tickets/05-ats-platform-survey.md) established that a
source must be fetchable with an ordinary unauthenticated GET returning JSON, carrying a
usable posting date and a usable location. That boundary is deliberately stricter than "the
public page can be parsed", and it is what ruled Workday out despite valuable coverage.

### A reframe is an admissible — likely — answer

Both sites are believed to be login-walled with bot protection. If so, the answer is **not**
"skip them". It is: mine their listed companies and feed the resulting board slugs to
adapters kelsa-hunt already has. Most YC and Wellfound companies run **Ashby, Greenhouse, or
Lever** — all three already supported, so this costs zero new fetcher code. Recommending
that path is a successful resolution of this ticket, not a failure.

### What to determine

- For each of Wellfound and YC Work at a Startup: is there an unauthenticated GET/JSON
  endpoint? Label findings **Documented**, **Observed <date>**, or **Inference**, as the
  predecessor research files do.
- If an endpoint exists: does it carry a dependable posting date and a parseable location,
  and can it be filtered or queried by UK location? Does it expose enough for a stable
  `uid` and an Opening Identity?
- Check each site's Terms of Service and `robots.txt`, and say plainly whether programmatic
  access is permitted. **If access is disallowed or requires authentication, stop and report
  that — do not attempt to bypass a login, rate limit, or bot protection.** This project
  runs on public unauthenticated endpoints only.
- If login-walled: is there a public, stable, machine-readable list of companies (YC's
  public company directory, Wellfound's public company pages)? How many are UK-based or have
  UK offices, and how many resolve to an ATS already supported?
- Note any UK-specific coverage gap these sources would fill that the existing 110-feed
  inventory does not — the Store already holds 1,405 confirmed-UK Records from current
  sources, so quantify the marginal gain rather than asserting it.

### Deliverable

A research file at `docs/wayfinder/uk-expansion/research/18-wellfound-yc-survey.md`, in the
style of [the ATS platform survey](../../research/05-ats-platform-survey.md): a bottom-line
recommendation first, explicit evidence labels, and a ranked effort-versus-coverage
judgement. Where the recommendation is "harvest their companies instead", include the
candidate slug list so
[the sponsor-company ticket](19-uk-sponsor-company-list.md) can consume it directly.

## Resolution

**Closed 2026-08-01.** Findings:
[Wellfound and YC Work at a Startup — GET/JSON Boundary Survey](../research/18-wellfound-yc-survey.md).

**The answer is the reframe.** Neither source passes the GET/JSON boundary, and in both cases
the operator has posted an explicit signal against programmatic access. Nothing was bypassed.

- **Wellfound — permanently declined for access reasons.** Every plain GET to `wellfound.com`
  returned `403` behind a DataDome challenge — including the public terms page and the
  robots-listed sitemap, so there was no document to evaluate. `api.wellfound.com/robots.txt`
  is `Disallow: /`.
- **YC Work at a Startup — permanently declined for access reasons.** `/companies`
  302-redirects an unauthenticated GET to the marketing homepage. A public SEO surface at
  `/jobs` exists but is `text/html` with a 29-row blob escaped in an HTML attribute, carries
  **no per-posting date**, and its `applyUrl` is a signup wall — the Rippling failure mode from
  [ticket 05](../../tickets/05-ats-platform-survey.md). Decisively, **YC's Terms of Use
  prohibit automated collection outright**, which overrides `workatastartup.com`'s permissive
  `robots.txt`. `api.ycombinator.com/robots.txt` is also `Disallow: /`.

Record both alongside 05's Workday entry so no future session re-derives this.

**The reframe delivered 36 verified boards** (35 companies) on existing adapters — 576 UK
openings under a strict country-marker test, 876 under a loose one, zero new adapter code, zero
collisions with the 109 configured slugs.

**Size the win honestly — the notification gain is small today.** Only **4** of those 576 pass
`classify()` at Score ≥5 (3 Graphcore graduate roles, 1 Cohere MTS); 16 under the loose test.
The storage gain is the real prize: 26 of 35 companies are absent from all 24,650 Records.

**Two findings that outrank the ticket's own question:**

1. **290 openings hang on how [ticket 15](15-eligible-region-boundary.md) resolves bare
   `London`.** 14 of 36 boards drop to **zero** UK openings under the strict test because those
   tenants omit any country marker. This reproduces the map's 385-Record delta on brand-new
   sources — independent confirmation that ticket 15 is the keystone.
2. **Wayve is live on Greenhouse *and* Ashby simultaneously** with byte-identical titles. Also
   found independently by [ticket 19](19-uk-sponsor-company-list.md).

**Verified independently before closing** (2026-08-01, via the repo's own fetchers): Graphcore
returned 225 postings / 111 UK-marker, carrying `2026 Graduate Silicon Engineer` and
`2026 Graduate Firmware Engineer` at Score Band **15** — matching the research exactly. Wayve
Ashby 107 postings / 30 UK-marker / 88 titles; Wayve Greenhouse 109 / **0** UK-marker / 90
titles, of which **88 are identical** to the Ashby set. The Greenhouse tenant emits bare
`London` (26 postings) and the Ashby tenant emits the country marker, so **the Ashby slug is the
correct pick for a second, verified reason.**

## Blocked by

_(nothing — frontier)_

## Related work

- [Survey which ATS platforms expose usable public job APIs](../../tickets/05-ats-platform-survey.md)
  — the GET/JSON boundary this reuses.
- [Find aggregator feeds worth adding beyond Simplify](../../tickets/07-aggregator-feeds.md)
  — prior aggregator survey; ambicuity was its only recommendation.
- [Fit the expanded Source Inventory to the scan-time budget](21-scan-time-budget.md)
  — consumes whatever this adds.
