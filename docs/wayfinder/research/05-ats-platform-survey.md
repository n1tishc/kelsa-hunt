# ATS Platform Public API Survey

**Decision use:** source-expansion budget for Kelsa-hunt  
**Researched:** 2026-07-30  
**Scope:** a company board must be fetchable with an unauthenticated, ordinary HTTP **GET** whose response is JSON. This is deliberately stricter than “the public career page can be parsed.” The age gate needs a usable date and the Bay Area filter needs a usable location.

## Bottom line

Add **SmartRecruiters**, **Workable**, and **Recruitee**. They are real, low-complexity GET/JSON board APIs with the two fields this project needs. Keep them as separate, small fetchers like Greenhouse/Lever/Ashby.

Do **not** add Workday, Rippling, Teamtailor, BambooHR, or JazzHR to the normal source configuration. Workday would add valuable Bay Area coverage, but its public board search is unauthenticated **POST**, not GET. The others require credentials, yield HTML, omit a dependable posting date, or depend on an undocumented build artifact. That is a different maintenance category and conflicts with the ticket’s cost boundary.

### Evidence labels

- **Documented** means the linked vendor documentation says it.
- **Observed 2026-07-30** means a read-only request to the linked live endpoint/board returned the stated result on that date. A live result is not a promise that a future request will do so.
- **Inference** is an implementation or coverage judgment, marked as such.

## Ranked support effort versus coverage gained

Coverage is a qualitative estimate of incremental *Bay Area new-grad SWE/MLE* opportunity, not a market-share claim. “Example” is evidence that a Bay Area employer/role is actually on the platform; it is not a claim of exclusivity or a directory of all customers.

| Rank | Platform | Plain unauthenticated GET JSON? | Implementation effort | Incremental Bay Area coverage | Recommendation |
|---|---|---:|---|---|---|
| 1 | SmartRecruiters | **Yes** | Low: list endpoint plus optional detail request | Medium. [Visa’s public board](https://jobs.smartrecruiters.com/Visa) is a Foster City–area enterprise example. | Add now |
| 2 | Workable | **Yes** | Low: one widget endpoint | Medium. [Renew Home’s board response](https://www.workable.com/api/accounts/renewhome?details=true) is live and includes San Francisco openings. | Add now |
| 3 | Recruitee | **Yes** | Low: one documented endpoint | Low–medium. [Aetherflux’s live board API](https://aetherflux.recruitee.com/api/offers/) includes San Carlos roles. | Add now |
| 4 | Workday | **No — POST only** | High if the constraint changes | High. [NVIDIA’s Santa Clara board](https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite) demonstrates why it is tempting. | Do not add under current rule; revisit only if POST is approved |
| 5 | Rippling | Technically a fragile Next.js data route; no stable public API | High | Low–medium. [Foundation](https://ats.rippling.com/foundation-robotics/jobs) has San Francisco jobs. | Do not add |
| 6 | Teamtailor | **No** | High (HTML scrape) | Unproven/low from primary-source sample | Do not add |
| 7 | BambooHR | **No** | High (HTML scrape; official API needs credentials) | Unproven/low from primary-source sample | Do not add |
| 8 | JazzHR | **No** | High (credentialed API/HTML) | Unproven/low from primary-source sample | Do not add |

The ordering after rank 3 is a *do-not-build* ordering, not a backlog. Workday alone merits a future decision because its coverage can justify intentionally broadening the transport rule; the others do not yet have comparable, verified Bay Area upside.

## Platforms to support

### 1. SmartRecruiters — supported

**URL and slug.** The documented public listing endpoint is:

```text
GET https://api.smartrecruiters.com/v1/companies/{companyIdentifier}/postings?limit=100&offset=0
GET https://api.smartrecruiters.com/v1/companies/{companyIdentifier}/postings/{postingId}
```

The vendor says `companyIdentifier` is the final segment of its default `https://careers.smartrecruiters.com/{identifier}` URL, and documents `limit`, `offset`, and the listing/detail endpoints in its [Posting API endpoint reference](https://developers.smartrecruiters.com/docs/endpoints). Use `limit=100` and advance `offset` until `offset + len(content) >= totalFound`; the same reference documents the pagination fields and calls out that list fields can be absent, with `ref` pointing at the detail resource.

**GET/JSON and fields.** Observed 2026-07-30, [a live list request](https://api.smartrecruiters.com/v1/companies/smartrecruiters/postings?limit=1) returned `200 application/json` with `content`, `totalFound`, a `releasedDate` ISO timestamp, and a structured `location` (`city`, `region`, `country`, `remote`, `hybrid`, `fullLocation`). The vendor’s own example documents the same `releasedDate` and location shape ([endpoints reference](https://developers.smartrecruiters.com/docs/endpoints)). This is enough for direct `posted` and deterministic location formatting; use the detail `ref` only when the list has omitted a required field.

**Rate limits/auth.** No numeric limit was found in the public endpoint documentation. The observed successful response did not expose `RateLimit-*` or `Retry-After` headers. Treat `429`, `401`, and `403` as a failed source fetch (do not close old Records), back off, and log them. There is a documentation conflict: the [Posting API overview](https://developers.smartrecruiters.com/docs/posting-api) says the product supports API-key authentication, while the live endpoint above succeeded without one. Therefore implement the observed public route, but do not assume every tenant remains public.

**Coverage and risks.** [Visa’s board](https://jobs.smartrecruiters.com/Visa) and [live API response](https://api.smartrecruiters.com/v1/companies/Visa/postings?limit=1) establish a notable Bay Area employer using the format. **Inference:** coverage is medium rather than high because it is useful enterprise coverage but no tenant discovery API is exposed; each company needs a known board URL/identifier. The identifier is brand/case-sensitive configuration, so migrations, rebrands, or a board made private can turn a formerly valid fetch into `0` or an error. Guard the configured slug with a non-empty/health expectation where the company formerly had openings; a clean `200` with `totalFound: 0` is otherwise a silent-zero hazard. Also preserve the vendor’s `releasedDate` verbatim—some old/republished records can have dates that are not useful as a “new opening” signal.

### 2. Workable — supported

**URL and slug.** Workable itself documents the public careers endpoints:

```text
GET https://www.workable.com/api/accounts/{account_subdomain}?details=true
GET https://www.workable.com/api/accounts/{account_subdomain}/locations
GET https://www.workable.com/api/accounts/{account_subdomain}/departments
```

See Workable’s [API troubleshooting article](https://help.workable.com/hc/en-us/articles/4903195036183-Troubleshooting-API-issues), which explicitly calls these alternate public endpoints, and its [career-page documentation](https://help.workable.com/hc/en-us/articles/115012944968-Comparing-careers-page-options), which identifies the hosted-board form as `apply.workable.com/{companyname}`. Derive the slug from that hosted board URL when one exists; do not try to infer it from the employer’s marketing domain. In the observed requests, the legacy URL redirected to `https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true`; follow redirects rather than hard-coding the redirect target.

**GET/JSON and fields.** Observed 2026-07-30, [Renew Home’s request](https://www.workable.com/api/accounts/renewhome?details=true) returned `200 application/json`. Its job objects include `title`, `shortcode`, `url`, `created_at` (date), and a `locations` array containing country, state/region, and city. The live response is a concrete San Francisco-area example. `created_at` is suitable for the age gate; store it as the source-provided date and do not claim it is an externally guaranteed “published at” timestamp. The public route may also provide `published_on`, but code must tolerate it being absent.

**Rate limits/auth.** Workable documents a **10 requests / 10 seconds** limit and `429` for its authenticated API ([official API FAQ](https://help.workable.com/hc/en-us/articles/115013356548-Workable-API-Documentation)). It does not separately publish a widget-endpoint quota. Apply the same conservative ceiling or slower, and honour `429`; observed public-widget responses had CORS enabled but no rate-limit headers. Do not use the private SPI `/jobs` API: Workable’s documentation says it is Bearer-token based.

**Coverage and risks.** [Renew Home’s hosted application](https://apply.workable.com/renewhome/) and the API above show a live Bay Area example. **Inference:** Workable is worth the same small-fetcher cost as SmartRecruiters, but coverage is limited to employers using the hosted board/widget. Custom-domain careers pages can conceal the underlying slug, and an empty `jobs` list can be a legitimate hiring lull or a stale/mistyped slug; do not automatically mark prior Records Closed on the first zero response. Redirects and widget versioning are a separate regression test target.

### 3. Recruitee — supported

**URL and slug.** The vendor’s Careers Site API documents this exact public route:

```text
GET https://{company}.recruitee.com/api/offers/
```

It says the endpoint returns published company jobs and that `{company}` is the careers-site subdomain ([`/offers/` reference](https://docs.recruitee.com/reference/offers)); the [API introduction](https://docs.recruitee.com/reference/intro-to-careers-site-api) explicitly says this candidate-facing API requires no authorization. `department` and `tag` are optional filters, not needed for a full scan.

**GET/JSON and fields.** Observed 2026-07-30, [Aetherflux’s endpoint](https://aetherflux.recruitee.com/api/offers/) returned `200 application/json` with an `offers` list. Each observed offer had stable id/guid/slug, `title`, `locations` with city/state/country and remote data, and ISO `created_at`, `published_at`, and `updated_at`. Prefer `published_at` for `posted`, then `created_at`; format every listed location rather than silently dropping multi-location jobs. This is directly compatible with the age and Bay Area rules.

**Rate limits/auth.** No numerical rate limit was found in the official Careers Site API documentation, and the successful response exposed no rate-limit headers. Use one board scan per configured company per run, exponential backoff for `429`/5xx, and report rather than close on failure.

**Coverage and risks.** [Aetherflux’s public career page](https://aetherflux.recruitee.com/) and API contain San Carlos jobs, establishing real local coverage. **Inference:** Recruitee is third because the API is exceptionally clean but its verified local target list is shorter than Workable’s/SmartRecruiters’. It shares the standard hosted-subdomain migration risk: `200 {"offers": []}` is syntactically successful and indistinguishable from a legitimate empty board without historical expectations. The endpoint only exposes published offers, so absence is a source observation—not a filled-role assertion.

## Platforms not to support under the current transport rule

### Workday — high-value exception, but POST not GET

**Observed 2026-07-30:** NVIDIA’s public [Workday board](https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite) derives a candidate-search endpoint from its host, tenant, and site path:

```text
https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs
```

`GET` to that URL returned `400 application/json`. An unauthenticated `POST` with `{"appliedFacets":{},"limit":1,"offset":0,"searchText":""}` returned `200 JSON`, including `jobPostings[].title`, `externalPath`, `locationsText`, and relative `postedOn` (observed: `"Posted Today"`). This is enough to establish that the board works without login, but it fails the plain-GET requirement and needs relative-date parsing plus a detail request/normalization for multi-location text.

Workday’s own Recruiting material describes the external Candidate Experience but does not publish this browser-search endpoint as a stable public API ([Workday Recruiting introduction](https://doc.workday.com/workday-education/en-us/course-manuals/recruiting-for-administrators/introduction-to-workday-recruiting.html)). No numeric public rate limit was found. **Inference:** Workday’s coverage is high enough to revisit separately, but only after an explicit decision to allow a POST-based, tenant/site-specific fetcher and its maintenance burden. Treat `400`, empty pages, and template changes as health failures; an old configured host/site can otherwise produce a silent loss of coverage.

### Rippling — HTML board; undocumented build-ID JSON is not an API

The public-board convention observed at [Foundation](https://ats.rippling.com/foundation-robotics/jobs) is `https://ats.rippling.com/{board-slug}/jobs`; its HTML contains job names and structured locations. The board page also exposed an unauthenticated Next.js data route on 2026-07-30:

```text
GET https://ats.rippling.com/_next/data/{buildId}/{board-slug}/jobs.json
```

For the then-current `{buildId}`, the response was JSON with ids, names, URLs, departments, and structured locations—but **no job posting timestamp**. The `buildId` is deployment-specific (the observed page supplied it) and can change at any release. This technically answers “can one get JSON?” with *yes, transiently*, but fails the supportability test: scrape HTML first to discover a build ID, then parse an undocumented internal payload, while still falling back to `first_seen` for age. That is not a 25-line fetcher.

Rippling’s official REST API documentation is credentialed (for example, [its getting-started guide](https://developer.rippling.com/documentation/rest-api/guides/data-getting-started)); no official public jobs API/rate policy was found. **Inference:** do not implement. Board slugs and the data-route build ID make migrations/deployments especially likely to look like zero jobs or a parse failure. The Foundation example proves some San Francisco coverage, not a stable integration contract.

### Teamtailor — official API requires a token; public page is HTML

The official [Teamtailor API](https://docs.teamtailor.com/) requires `Authorization: Token token=…` and `X-Api-Version`; its `/v1/jobs` documentation says a public-read key can read jobs and locations, but it is still a tenant-managed secret. Observed 2026-07-30, unauthenticated `/v1/jobs` returned `401` after supplying the required version header. The vendor documents a 50 requests/10 seconds limit for that credentialed API, not a public board route.

The public career-page form, illustrated by [Teamtailor’s own jobs page](https://career.teamtailor.com/jobs), is server-rendered HTML with location text and no dependable displayed posting date. Thus neither a plain GET JSON feed nor the required fields are available without credentials/scraping. **Inference:** no added source coverage justifies an HTML parser here. A custom domain or a moved company board will be indistinguishable from a missing slug unless explicitly monitored.

### BambooHR — official ATS API is authenticated; career page is HTML

BambooHR documents `GET https://{companyDomain}.bamboohr.com/api/v1/applicant_tracking/jobs`, but it says the caller must be authenticated and have ATS-settings access; the reference lists Basic credentials and `401`/`403` responses ([Get Job Summaries](https://documentation.bamboohr.com/reference/get-job-summaries)). Observed 2026-07-30, an unauthenticated request did not yield a usable board JSON response. Its public `/careers/…` pages are HTML rather than this API.

The official API can sort by `created`, but that is irrelevant without tenant credentials. No verified public GET/JSON board, public-board rate limit, or material Bay Area tech target was found from first-party sources. **Inference:** do not spend an HTML-scraper budget; hosted subdomains/custom careers links add the usual migration and silent-zero risk.

### JazzHR — public-looking API rejects requests without an API key

Observed 2026-07-30, `GET https://api.resumatorapi.com/v1/companies/jazzhr/jobs` returned `401 {"error":"apikey not set"}`. That is the platform’s live API domain, not a public board API. No first-party documentation or live public GET endpoint establishing unauthenticated jobs, structured locations, and a posting date was found in this research pass.

JazzHR hosted application pages may be crawlable HTML, but that does not meet the ticket criterion. No public rate-limit evidence or material Bay Area company coverage was verified from primary sources. **Inference:** treat JazzHR as unsupported until the vendor publishes a candidate-facing JSON contract; do not mistake a 401, a changed company slug, or an HTML application page for a successful empty scan.

## Implementation recommendation

1. Add `fetch_smartrecruiters(slug)`, `fetch_workable(slug)`, and `fetch_recruitee(slug)` only. Each should return `(records, ok)` and use the same failure rule as existing fetchers: failures—including auth/rate-limit failures—must **not** close records for that source.
2. Store the platform’s immutable job ID (SmartRecruiters `id`/`uuid`, Workable `shortcode`, Recruitee id/guid) in the UID. Keep the original public job URL as the apply URL. Normalize all locations into a single searchable string while preserving all locations in the original Record if the schema permits.
3. Prefer source dates in this order: SmartRecruiters `releasedDate`; Workable `published_on` then `created_at`; Recruitee `published_at` then `created_at`. If absent, retain Kelsa-hunt’s established `first_seen` fallback—do not manufacture a date.
4. Add a small source-health check before enabling any new slug: endpoint must be JSON, return the expected top-level shape, and have a plausible job count. Alert/log on a transition from a historically non-empty board to zero; never automatically treat that as all jobs Closed. This directly addresses the configured-slug migration/silent-zero warning in the project README/ticket.
5. Reconsider Workday only through a separate ADR/ticket that explicitly permits POST. Do not quietly relax the GET-only boundary for one desirable employer.

## Remaining uncertainty

No vendor publishes a durable public directory of every customer board, so coverage cannot be made exhaustive from primary sources. “No numeric rate limit found” means precisely that—not that a platform is unlimited. Public board settings are tenant-controlled and can change after this survey. Finally, the three approved APIs were verified against individual live tenants on 2026-07-30; add a lightweight integration fixture/health test before relying on any new configured slug.
