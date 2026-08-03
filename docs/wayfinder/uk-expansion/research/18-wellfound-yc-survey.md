# Wellfound and YC Work at a Startup — GET/JSON Boundary Survey

<!-- wayfinder:research -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md) ·
Ticket: [18-wellfound-yc-source-survey](../tickets/18-wellfound-yc-source-survey.md)

**Decision use:** UK source-expansion budget for kelsa-hunt
**Researched:** 2026-08-01
**Scope:** the boundary set by [the ATS platform survey](../../research/05-ats-platform-survey.md) —
a source must be fetchable with an ordinary **unauthenticated HTTP GET whose response is JSON**,
carrying a usable posting date and a usable location. That rule is what ruled Workday out despite
valuable coverage, and it is applied unchanged here.

## Bottom line

**Neither source passes, and neither should be attempted.** Both fail the 05 boundary, and in both
cases the site operator has posted an explicit signal against programmatic access. No login, rate
limit, or bot protection was bypassed during this survey.

- **Wellfound** — every plain GET to `wellfound.com` in this pass returned **`403` with a DataDome
  bot-protection challenge**, including the public terms page and the robots-listed sitemap. Its API
  host publishes `Disallow: /`. There is no endpoint to evaluate against 05, and probing further
  would mean defeating bot protection. **Stop.**
- **YC Work at a Startup** — the company/job browser at `workatastartup.com/companies` **302-redirects
  an unauthenticated GET to the marketing homepage**; the site returns `406` to
  `Accept: application/json`. A genuinely public SEO surface does exist at `/jobs` and `/jobs/l/{role}`,
  but it is `text/html` with a 29-row JSON blob escaped inside an HTML attribute, **carries no
  per-posting date**, and its `applyUrl` is a signup wall. That is the Rippling failure mode from 05,
  not a feed. Independently, **YC's Terms of Use prohibit automated collection outright.** **Stop.**

**Take the reframe.** Harvest the ATS boards of the companies these platforms surface. This survey
verified **36 board slugs** (35 companies) on adapters kelsa-hunt already has (`greenhouse`, `ashby`,
`lever`, `smartrecruiters`), together exposing **576 UK openings under the map's strict country-marker
test — 876 under its loose test** on 2026-08-01, **zero of them duplicating the 109 slugs already in
`sources.json`**, at **zero new adapter code**.

**But size the win honestly, and note it is gated on ticket 15.** Those UK openings yield only
**4 Records that pass `classify()` at Score ≥ 5 under the strict test** (3 Graphcore graduate
engineering roles, 1 Cohere MTS) — **16 under the loose test**. And **14 of the 36 boards drop to zero
UK openings under the strict test** (11 Ashby, 2 Greenhouse, 1 Lever), because those tenants write bare
`London` with no country marker. So the reframe is a large win for **recall-first UK storage**, a small one for
**notification volume**, and its true size is decided by
[the Eligible Region boundary ticket](../tickets/15-eligible-region-boundary.md) — this survey supplies
the first measurement of what that decision is worth on *new* sources. Recommendation: adopt the
reframe, and treat notification yield as a question for
[the classifier ticket](../tickets/17-classify-uk-titles.md) and the autumn scheme season.

### Evidence labels

- **Documented** — the linked first-party document says it.
- **Observed 2026-08-01** — a read-only request returned the stated result on that date. A live result
  is not a promise a future request will do so. (Requests were made in the evening of 2026-08-01
  local time; some responses carried a `2026-08-02` UTC `Date` header.)
- **Inference** — an implementation or coverage judgement, marked as such.

## Access permission: robots.txt and Terms of Service

`robots.txt` is per-host, so every host actually requested was checked.

| Host | robots.txt (**Observed 2026-08-01**) | Verdict |
|---|---|---|
| `wellfound.com` | `200`. Does **not** disallow `/jobs` or `/company/*/jobs`; does disallow `/_jobs/`, `/*?role=*`, `/*?jobId=*`, `/*?jobSlug=*`, `/auth/`, `/embed/`, `/jobs/applications` | robots is permissive for job pages — but the host answers `403` regardless (below) |
| `api.wellfound.com` | `200`, body is exactly `User-agent: *` / `Disallow: /` | **Programmatic access disallowed** |
| `www.workatastartup.com` | `200`, body is exactly `User-Agent: *` / `Disallow:` — i.e. nothing disallowed | robots is fully permissive; **ToS is not** (below) |
| `www.ycombinator.com` | `200`. `Disallow: /verify/*`, `Disallow: /library?*`, **`Disallow: /companies?*`**, then `Allow: /` | the company directory is crawlable only without a query string |
| `api.ycombinator.com` | `200`, body is `User-Agent: *` / `Disallow: /` | **Programmatic access disallowed** — the YC company-directory API host is off-limits |
| `boards-api.greenhouse.io` | `200`, `Disallow: /embed/` only | board API permitted (already used by this repo) |
| `api.lever.co` | `200`, `Allow: /`, `Crawl-delay: 1` | permitted; honour the 1s crawl delay |
| `api.ashbyhq.com` | `401 Unauthorized` — no robots document served | see note below |

**Ashby robots note (Inference).** RFC 9309 §2.3.1.3 treats a `4xx` on `robots.txt` as "unavailable"
and permits access; the older Google convention treated `401`/`403` as a full disallow. The ambiguity
is noted rather than resolved: this repo already fetches `api.ashbyhq.com/posting-api/job-board/{slug}`
for 31 configured slugs, so the survey follows established practice here and does not relitigate it.

### Terms of Service

**Y Combinator — Documented.** The Terms of Use published at
[ycombinator.com/legal](https://www.ycombinator.com/legal/) state, verbatim:

> Except as expressly authorized by Y Combinator, you agree not to modify, copy, frame, scrape, rent,
> lease, loan, sell, distribute or create derivative works based on the Site or the Site Content, in
> whole or in part … **In connection with your use of the Site you will not engage in or use any data
> mining, robots, scraping or similar data gathering or extraction methods.** If you are blocked by
> Y Combinator from accessing the Site (including by blocking your IP address), you agree not to
> implement any measures to circumvent such blocking.

**This is a direct conflict with `workatastartup.com`'s fully permissive `robots.txt`, and the
stricter document governs.** A permissive `Disallow:` is the absence of a crawl restriction, not a
grant of permission.

One scoping caveat, stated rather than resolved in the convenient direction: the Terms define the
"Site" as "the Y Combinator website (**including all subdomains**)", and `workatastartup.com` is a
separate domain, not a subdomain of `ycombinator.com`. However — **Observed 2026-08-01** — the same
`legal/` page's Privacy Policy defines its Site as "all websites to which this Privacy Policy is
posted" and expressly governs "Work at a Startup Information (WaaS)"; and WaaS login/signup is
handled by `account.ycombinator.com`. **Inference:** WaaS sits inside YC's legal umbrella, the
anti-scraping clause is intended to reach it, and building a fetcher against it would be a bad-faith
reading. Treat it as prohibited.

**Wellfound — not retrievable.** `https://wellfound.com/terms` returned **`403`** to a plain GET and
to a second independent fetcher (**Observed 2026-08-01**). The ToS text is therefore *not* quoted here
and nothing is asserted about its contents. Two first-party signals point the same direction anyway:
`api.wellfound.com/robots.txt` says `Disallow: /`, and the whole `wellfound.com` host answers
unauthenticated GETs with a bot-protection challenge. **Programmatic access is not permitted.**

## Wellfound — fails: the host will not serve a plain GET at all

**Observed 2026-08-01.** With an ordinary browser `User-Agent` and no cookies:

| Request | Result |
|---|---|
| `GET https://wellfound.com/jobs` | `403 text/html`, 1,711 bytes |
| `GET https://wellfound.com/company/wellfound/jobs` (the URL Wellfound's own robots.txt advertises) | `403 text/html`, 1,711 bytes |
| `GET https://wellfound.com/terms` | `403 text/html`, 1,711 bytes |
| `GET https://wellfound.com/sitemap.xml.gz` (robots-listed) | `403 text/html`, 1,711 bytes |
| `GET https://wellfound.com/graphql` with `Accept: application/json` | `403 text/html`, 38,477 bytes |

Every 1,711-byte body was the same DataDome interstitial — `Please enable JS and disable any ad
blocker`, a `ct.captcha-delivery.com/c.js` loader, and a `geo.captcha-delivery.com` CAPTCHA host —
served with response headers `x-datadome: protected`, `x-dd-b: 2`, a year-long `datadome` cookie, and
`server: cloudflare`.

**Conclusion.** There is nothing to test against 05: no status-200 response, no JSON, no posting date,
no location, no `uid` material, no Opening Identity. The only way past this is to solve or evade a
CAPTCHA, which the ticket forbids and this project's posture forbids. **No further probing was done.**

**Inference on the underlying architecture.** The presence of a `/graphql` route is consistent with
Wellfound serving job search over POSTed GraphQL rather than GET — the *exact* transport that ruled
Workday out in 05. This is offered as a judgement, not a measurement: the 403 prevented confirming
the request shape, and confirming it is not worth defeating bot protection for.

## YC Work at a Startup — fails: login-walled browser, dateless public teaser

**Observed 2026-08-01.** `workatastartup.com` is a Rails + Inertia app that ships page props as JSON
escaped inside a `data-page` HTML attribute. Unauthenticated behaviour:

| Request | Result |
|---|---|
| `GET /companies` | **`302` → `https://www.workatastartup.com/`** — the job browser is login-walled |
| `GET /companies?role=eng` | `302` → `/` |
| `GET /directory` | `301` → `/companies` → `302` → `/` |
| `GET /companies/fetch?page=1` | `302` → `www.ycombinator.com/companies/fetch` |
| any path with `Accept: application/json` | **`406 Not Acceptable`, zero bytes** — no JSON representation is offered |
| any path with no `Accept` header | `406` |
| `GET /` | `200 text/html` — homepage props contain `"logout": null` and `"login": "https://account.ycombinator.com/magic?continue=…"`, confirming no session |
| `GET /jobs` | `200 text/html`, 68 KB |
| `GET /jobs/l/software-engineer` | `200 text/html`, 68 KB |

### The public `/jobs` surface, measured against 05

`/jobs` and the ten `/jobs/l/{role}` pages are genuinely public. Each embeds exactly **29 job objects**
with these fields (**Observed 2026-08-01**):

```text
id, title, jobType, location, roleType, salary,
companyName, companySlug, companyBatch, companyOneLiner, companyLogoUrl,
companyLastActiveAt, applyUrl
```

It fails the boundary on four independent counts:

1. **Not JSON.** `Content-Type: text/html`. The payload is HTML-entity-escaped JSON inside an
   attribute value. Reaching it means parsing HTML first — the disqualifier 05 applied to Rippling.
2. **No posting date.** There is no `posted`, `created_at`, or `published_at`. The only temporal field
   is `companyLastActiveAt`, a **company-level relative string** — observed values included
   `"about 12 hours ago"`, `"24 days ago"`, `"about 1 year ago"`, and `null` for **7 of 29** rows on the
   engineering page. It is not a posting date for the requisition and cannot drive the 21-day Freshness
   gate. kelsa-hunt would fall back to `first_seen` for every row.
3. **No queryable UK filter and no pagination.** 29 rows, role-faceted only. There is no location
   parameter and no cursor; the browsable filter lives behind the `/companies` login wall.
4. **No usable apply URL or Opening Identity.** `applyUrl` is
   `account.ycombinator.com/authenticate?continue=…signup_job_id={id}` — a signup wall, not the
   posting. The numeric `id` would give a stable `uid`, but the destination a Candidate would receive
   is a login page.

### And the role mix is structurally wrong for this project

**Observed 2026-08-01**, on `/jobs/l/software-engineer` (the engineering facet, 29 rows):

- **21 of 29** titles carry a senior/staff/founding/lead/head marker.
- **0 of 29** carry any new-grad, graduate, junior, entry-level, or `Engineer I` signal.
- **2 of 29** were UK (`London, England, GB` — Seeing Systems, batch W26, two hardware roles).

**Inference.** Work at a Startup is a seed-stage founding-engineer marketplace. Its supply is the
inverse of what kelsa-hunt's Score Band 10 exists to catch. Even if the transport problem were solved
and the ToS permitted it, the incremental *graduate* yield would be near zero.

## The reframe: harvest their companies' ATS boards

### How this candidate list was built, and what it is not

Because YC's ToS prohibits automated data gathering and `api.ycombinator.com` publishes `Disallow: /`,
**the list below was not harvested from YC's or Wellfound's directories.** It was assembled from prior
knowledge of UK-hiring startups and scale-ups, then **every row was verified by a live read-only GET to
the platform's public board API** — the same endpoints `job_alert.py` already calls
(`boards-api.greenhouse.io/v1/boards/{slug}/jobs`, `api.ashbyhq.com/posting-api/job-board/{slug}`,
`api.lever.co/v0/postings/{slug}?mode=json`,
`api.smartrecruiters.com/v1/companies/{slug}/postings`).

Consequences to carry into [the sponsor-company ticket](../tickets/19-uk-sponsor-company-list.md):

- **The slug and the UK counts are Observed.** No row was inferred from a careers-page URL. **325
  candidate slugs were probed** — 277 across two rounds on Greenhouse/Ashby/Lever, plus 48 on
  SmartRecruiters/Workable/Recruitee. The 36 boards below are the ones that returned `200`, valid JSON,
  a non-zero job count, and at least one location matching a UK marker.
- **YC / Wellfound membership is *not* verified for these companies.** Verifying it programmatically is
  precisely what the ToS forbids. The only YC-listed UK company this survey actually observed is
  **Seeing Systems (W26, London)**, from the public `/jobs` teaser — and it has no ATS board in the
  supported set. A human reading YC's directory in a browser is not automated collection, so ticket 19
  can add batch annotations that way if it wants them; this survey does not fabricate them.
- **The list is a verified sample, not exhaustive.** No vendor publishes a directory of customer
  boards, so slug discovery is guesswork plus verification. Absence from this table is not evidence a
  company has no board.

### Verified candidate boards — Observed 2026-08-01

Both of the map's UK tests are reported, because the gap between them turns out to be the dominant
finding on these boards:

- **UK — loose** matches a UK country marker *or* a bare UK city name. This is the map's permissive
  sweep, and it carries the map's known false-positive risk: it wrongly caught **10 postings** here,
  all `Cambridge, MA` or US-state variants (Isomorphic Labs 4, Cohere 4, ElevenLabs 2).
- **UK — strict** requires an explicit UK country marker (`United Kingdom`, `UK`, `GB`, `England`,
  `Scotland`, `Wales`, `Northern Ireland`). **Inference:** this mirrors the criterion the map *describes*
  for its 1,405-Record baseline ("an explicit UK country marker is required"), but the map does not
  publish its regex, so the correspondence is a judgement, not a verified equivalence. Every
  strict-vs-loose number below inherits that caveat.

**"Pass `classify()` ≥5"** ran the repo's **current** classifier — pre-[ticket
17](../tickets/17-classify-uk-titles.md) — over the strict-UK titles.

| Company | Platform | Slug | Openings (all regions) | UK — loose | UK — strict | Pass `classify()` ≥5 (strict) |
|---|---|---|---:|---:|---:|---:|
| Wise | smartrecruiters | `Wise` | 406 | 148 | 148 | 0 |
| Graphcore | greenhouse | `graphcore` | 225 | 111 | 111 | **3** |
| SumUp | greenhouse | `sumup` | 372 | 76 | 76 | 0 |
| ElevenLabs | ashby | `elevenlabs` | 224 | 66 | 55 | 0 |
| Monzo | greenhouse | `monzo` | 72 | 54 | 39 | 0 |
| Wayve | ashby | `wayve` | 107 | 30 | 30 | 0 |
| Ocado Group | greenhouse | `ocadogroup` | 50 | 23 | 23 | 0 |
| n8n | ashby | `n8n` | 37 | 21 | 21 | 0 |
| Tide | greenhouse | `tide` | 105 | 17 | 17 | 0 |
| GoCardless | greenhouse | `gocardless` | 30 | 13 | 13 | 0 |
| Cohere | ashby | `cohere` | 142 | 42 | 12 | **1** |
| Duffel | ashby | `duffel` | 11 | 8 | 5 | 0 |
| Synthesia | ashby | `synthesia` | 76 | 28 | 4 | 0 |
| Faire | greenhouse | `faire` | 72 | 4 | 4 | 0 |
| TrueLayer | greenhouse | `truelayer` | 10 | 4 | 4 | 0 |
| Deepgram | ashby | `deepgram` | 77 | 4 | 3 | 0 |
| Griffin | ashby | `griffin` | 3 | 3 | 3 | 0 |
| PolyAI | greenhouse | `polyai` | 15 | 3 | 3 | 0 |
| Lindus Health | ashby | `lindus` | 4 | 2 | 2 | 0 |
| Improbable | ashby | `improbable` | 9 | 4 | 1 | 0 |
| Lightdash | ashby | `lightdash` | 5 | 4 | 1 | 0 |
| Poolside | ashby | `poolside` | 16 | 1 | 1 | 0 |
| Legora | ashby | `legora` | 274 | 31 | **0** | 0 |
| Wayve | greenhouse | `wayve` | 109 | 31 | **0** | 0 |
| Multiverse | ashby | `multiverse` | 25 | 25 | **0** | 0 |
| Isomorphic Labs | greenhouse | `isomorphiclabs` | 23 | 22 | **0** | 0 |
| Lovable | ashby | `lovable` | 63 | 21 | **0** | 0 |
| Encord | ashby | `encord` | 34 | 20 | **0** | 0 |
| Vertice | ashby | `vertice` | 32 | 13 | **0** | 0 |
| Granola | ashby | `granola` | 16 | 9 | **0** | 0 |
| Orbital | ashby | `orbital` | 29 | 9 | **0** | 0 |
| Quantexa | ashby | `quantexa` | 32 | 9 | **0** | 0 |
| Moonpig | lever | `moonpig` | 11 | 8 | **0** | 0 |
| Basecamp Research | ashby | `basecamp-research` | 6 | 6 | **0** | 0 |
| StackOne | ashby | `stackone` | 5 | 4 | **0** | 0 |
| Sylvera | ashby | `sylvera` | 3 | 2 | **0** | 0 |
| **Totals (36 boards / 35 companies)** | | | **2,730** | **876** | **576** | **4** |

**The strict/loose gap is the headline structural finding.** 14 of the 36 boards report **zero**
strict-UK openings while showing 2–31 loose-UK ones, because their `location` field carries a bare city
(`"London "`, `"Edinburgh "`) with no country marker. The 14 break down as **11 Ashby, 2 Greenhouse
(`wayve`, `isomorphiclabs`), 1 Lever (`moonpig`)** — so this is a **tenant** convention, not a platform
one, and no platform can be trusted to supply a country.

The loose-minus-strict delta is **300 openings**. Ten of those are the US city collisions above, which
fail *any* UK test; the remaining **290 are bare-UK-city openings whose eligibility depends entirely on
how [ticket 15](../tickets/15-eligible-region-boundary.md) resolves bare `London`** — the same
385-Record delta the map already measured on existing sources, reproduced on new ones. Wayve is the
clean controlled comparison: its Greenhouse tenant writes bare `London` (0 strict), its Ashby tenant
writes `London, United Kingdom` (30 strict), for essentially the same requisitions.

**Dates are universally present — Observed 2026-08-01.** Counted over *every* loose-UK row, not a
spot-check: a per-posting date field was present on **728/728** rows (Ashby 362/362 `publishedAt`,
Greenhouse 358/358 `updated_at`, Lever 8/8 `createdAt`) plus **148/148** `releasedDate` on Wise. All four
field names are already handled by the existing fetchers, so **the reframe adds no date-parsing work.**
Note the Greenhouse list endpoint supplies `updated_at`, not an original publish date — a pre-existing
property of that adapter, not something these slugs introduce.

**Zero duplicates — Observed 2026-08-01.** Set intersection of the 36 proposed `platform:slug` pairs
against all 109 entries in `sources.json` (greenhouse 73, ashby 31, lever 1, smartrecruiters 1,
workable 1, recruitee 1, ambicuity 1) is **empty**, case-insensitively as well as exactly.

### Marginal gain over the existing 1,405 confirmed-UK Records

The map's baseline is 1,405 confirmed-UK Records accumulated from 110 feeds (Simplify 968, Greenhouse
573, Ashby 196, Lever 39, Ambicuity 14), topped by Databricks, Palantir, Sierra, Intercom, Stripe,
Anthropic, GitLab. That is a **cumulative historical** count; the 576/876 above are **currently live**
openings. They are not the same denominator and should not be subtracted from one another.

The 36 boards cover **35 distinct companies** (Wayve appears on two platforms — see Hazards). Measured
against the local 24,650-Record store (**Observed 2026-08-01**):

- **9 of the 35 companies appear in the store at all** — Graphcore 6, ElevenLabs 3, PolyAI 3,
  Quantexa 3, Cohere 2, Encord 2, Sylvera 2, Wise 2, Faire 1.
- Those 9 account for **24 Records total, 14 of them confirmed-UK** (Graphcore 6, Quantexa 3, Sylvera 2,
  Wise 2, PolyAI 1).
- All 24 arrived incidentally via aggregators: **Simplify 21, Ambicuity 3**. Not one came from a
  configured board.
- **26 of the 35 companies are wholly absent from 24,650 Records.**

So the storage gain is real and large: **576 strict-UK (876 loose-UK) live openings against 14 UK
Records the current inventory reaches for the same companies.** These are UK-headquartered or UK-engineering employers
(Monzo, Wise, GoCardless, Tide, TrueLayer, Ocado, Graphcore, Wayve, Isomorphic Labs, Synthesia,
Multiverse, Moonpig) that the existing US-curated inventory structurally does not cover.

### The notification gain is small today — and that is the honest headline

Under the **strict** test, **4 of 576 UK openings** pass the current classifier at Score ≥ 5:

| Score | Board | Title |
|---:|---|---|
| 15 | `greenhouse:graphcore` | 2026 Graduate Firmware Engineer |
| 15 | `greenhouse:graphcore` | 2026 Graduate Silicon Engineer |
| 5 | `greenhouse:graphcore` | Graduate Silicon Engineer |
| 5 | `ashby:cohere` | Member of Technical Staff, Search |

Under the **loose** test the count is **16 of 876** — the same 4 plus 10 more Cohere
`Member of Technical Staff` titles (Modeling, Post-Training, MLE (UK/EU), Pre-Training Data, …),
`ashby:encord` *Commercial Associate, Physical AI*, and `ashby:quantexa` *Associate Data Engineer*.
**Inference:** 11 of the 16 loose passes are Cohere MTS titles, which the MTS rule admits at Band 5 by
design and which CONTEXT.md already documents as carrying no title-only seniority signal. So the
genuinely new-grad-shaped yield across all 36 boards today is **3 Graphcore requisitions**.

Widening the search to *any* early-career vocabulary across all 876 loose-UK titles found only
**29 matches**, and 25 of those are non-engineering `Analyst`/`Associate` roles (`Senior Data Analyst`,
`Lead Product Analyst`, `Carbon Analyst`). Wise's 148 UK postings produced **zero** classifier passes
and 29 `Analyst` titles, every one of them senior or lead.

Three consequences, all worth carrying forward:

- **The Band 5 noise the map predicted is confirmed and quantified.** Widening `ROLE_MATCH` for UK
  vocabulary in [ticket 17](../tickets/17-classify-uk-titles.md) will admit UK `Associate`/`Analyst`
  titles from non-engineering functions. Graphcore's `Graduate SoC Architect` is the counter-example
  that argues for widening anyway — a genuine graduate engineering role currently rejected as "not an
  eng/ML role".
- **This is measured at the seasonal trough.** 2026-08-01 is off-season for UK graduate schemes, which
  open in autumn. Graphcore already has "2026 Graduate …" reqs live, which is evidence the boards *do*
  carry schemes when the season opens. **Inference:** re-measuring these same 36 boards in
  October would give a materially different Band 10 count. The map already lists this fog under
  "Whether the 21-day Freshness gate suits UK hiring rhythms"; this survey supplies the boards to
  measure it against.
- **`sources.json` curation, not filtering, is doing the work here.** These are exactly the companies
  the map's "hires internationals is source curation" decision was written for.

### Hazards found while verifying

- **Wayve is live on two platforms at once.** `greenhouse:wayve` (109 openings, 31 loose-UK) and
  `ashby:wayve` (107 openings, 30 loose-UK) both returned `200` with data, and **25 of the loose-UK
  titles are byte-identical across the two**. The Opening Identity registry is platform-scoped, so it
  *cannot* collapse a Greenhouse Record against an Ashby Record — configuring both would produce ~25
  duplicate Records and duplicate notifications. **Configure `ashby:wayve` only**: it is the tenant that
  writes `London, United Kingdom`, so it survives the strict region test while the Greenhouse tenant's
  bare `London` does not. This is a live instance of the map's open question "Cross-post identity under
  UK/EU ATS tenants", and it was found on the first company checked that had migrated.
- **Ashby's `location` field routinely omits the country.** Fourteen boards report bare `"London "` or
  `"Edinburgh "` with nothing else. Any per-slug health check that asserts "this board yields UK
  Records" will read as broken on those tenants until ticket 15 settles bare-city handling. Note the
  inconsistency is per-tenant, not per-platform: `ashby:wayve`, `ashby:duffel`, and `ashby:lindus` do
  emit an explicit country.
- **US/UK city collisions are live on these boards too.** The loose test wrongly admitted 10 postings —
  `Cambridge, MA` at Isomorphic Labs (4) and Cohere (4), plus 2 US-state variants at ElevenLabs. Exactly
  the failure the map recorded for `Cambridge, MA` (34), `Birmingham, AL` (17) and `Brighton, CO` (17)
  in existing data.
- **The silent-zero hazard from 05 applies unchanged.** `ashby:hex` and `ashby:snyk` returned
  `200 {"jobs": []}` — syntactically successful, indistinguishable from a healthy empty board.
  `greenhouse:cleo` (4 openings, 0 UK) and `ashby:peec` (37 openings, 0 UK) are real boards with no
  current UK presence. Neither state should ever be read as "all Records Closed".
- **Small boards are volatile.** `ashby:sylvera` (3), `ashby:griffin` (3), `ashby:lindus` (4),
  `ashby:lightdash` (5), `ashby:stackone` (5) are each a handful of openings. **Inference:** they will
  legitimately hit zero, so a non-empty health expectation must be per-slug rather than global.
- **Major UK employers are missing because they use ruled-out platforms.** Revolut, Starling,
  Checkout.com, Deliveroo, Snyk, Darktrace, Trainline, Depop, Onfido and Curve returned `404` on every
  Greenhouse/Lever/Ashby/SmartRecruiters/Workable/Recruitee slug variant tried. **Inference:** several
  run Workday or bespoke career sites. Workday is permanently out under 05, so this is a coverage
  ceiling, not a backlog item.

## Ranked effort versus coverage

Coverage is incremental *UK graduate/entry-level engineering* opportunity — a qualitative estimate
except where a number is given.

| Rank | Option | Plain unauthenticated GET JSON? | Effort | Incremental UK coverage | Recommendation |
|---|---|---:|---|---|---|
| 1 | **ATS boards of UK-hiring startups** (the 36 verified slugs) | **Yes** — existing adapters, unchanged | **Zero new adapter code**; ~36 config lines, +36 fetches/scan | **576 strict-UK (876 loose) live openings; 4 pass `classify()` strictly, 16 loosely; 26 of 35 companies absent from 24,650 Records** | **Adopt.** Feed the table to ticket 19 |
| 2 | Re-measure the same 36 boards in autumn | Yes | One query, no code | Unknown but plausibly much higher Band 10 | Do it after ticket 17 lands |
| 3 | **YC Work at a Startup** `/jobs` public teaser | **No** — `text/html`, JSON escaped in an attribute | High: HTML parse, **no posting date**, 29 rows, no pagination, no UK filter, signup-wall apply URL | ~2 UK rows observed, 0 entry-level of 29 engineering rows | **Do not build.** Fails 05 four ways **and** YC's ToS prohibits it |
| 4 | YC public company directory as a slug source | Host publishes `Disallow: /` | — | Would only ever be a *company* list: no per-role date, no per-role location — fails 05 independently of transport | **Do not build.** ToS-prohibited; and a directory is not a feed |
| 5 | **Wellfound** (any surface) | **Unknown — host returns `403`** | Would require defeating DataDome/CAPTCHA | Unmeasurable | **Do not build. Do not probe further.** |

Ranks 3–5 are a *do-not-build* ordering, not a backlog. Unlike Workday in 05 — which was withheld only
pending an explicit decision to permit POST — **nothing here is revisitable by relaxing a transport
rule.** Wellfound and YC are blocked by the operators' own access decisions, so revisiting would
require a *permission* change (published API, explicit authorisation), not a kelsa-hunt policy change.

## Implementation recommendation

1. **Do not write a Wellfound or a Work-at-a-Startup fetcher.** Record both as permanently declined for
   access reasons, alongside 05's Workday entry, so a future session does not re-derive this.
2. **Hand the 36-row table to [ticket 19](../tickets/19-uk-sponsor-company-list.md)** as the verified
   input it consumes. All slugs and UK counts are Observed 2026-08-01; **no YC/Wellfound membership
   claim is attached to any row** — add those manually if the ticket wants them.
3. **Pick one Wayve board, not both.** Then add a check that flags any company configured on two
   platforms, since the platform-scoped Opening Identity registry cannot dedup across them.
4. **Add the per-slug health expectation 05 already asked for** before enabling any of these. Several
   boards hold 3–6 openings; a global "non-empty" rule will produce false alarms, and a `200` with an
   empty list must never close Records.
5. **Re-run the Score measurement after tickets 15 and 17.** The 4-of-576 / 16-of-876 split is the
   pre-widening baseline, and it moves on *both* tickets: ticket 15 decides whether the 300 bare-`London`
   openings count at all, ticket 17 decides what `ROLE_MATCH` admits. Graphcore's
   `Graduate SoC Architect` — currently rejected as "not an eng/ML role" — is the concrete test case for
   the widened classifier.
6. **Report the fetch-count delta to
   [the scan-time budget ticket](../tickets/21-scan-time-budget.md):** 109 → 145 configured feeds,
   +36 requests per scan, plus 4 extra pagination requests for Wise's 406 postings. Lever asks for
   `Crawl-delay: 1`.

## Remaining uncertainty

The 403 wall means **nothing is known** about Wellfound's actual job transport — the GraphQL/POST
reading is Inference, and it stays Inference. YC's ToS scope over `workatastartup.com` rests on the
Privacy Policy's wider "Site" definition rather than the Terms' own subdomain clause; that reading is
Inference too, chosen deliberately as the conservative one.

On the reframe: the 36 boards are a verified sample, not a census, and slug discovery has no
first-party directory to draw on, so unknown UK companies on supported platforms certainly remain. Every
count is a single-moment observation of tenant-controlled configuration and will drift. The 576/4 (or
876/16) split is measured at the UK graduate-scheme seasonal trough, which is the single largest source of doubt about
how much notification volume this actually buys — and the reason recommendation 2 exists. Finally, the
Simplify overlap on these companies was measured against the local store's `company` strings only;
title-level cross-post overlap between Simplify and these boards was not measured and will reduce the
apparent new-Record count somewhat.
