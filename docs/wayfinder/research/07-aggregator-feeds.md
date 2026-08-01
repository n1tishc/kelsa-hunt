# Alternative New-Grad Job Feed Research

<!-- wayfinder:research -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Decision

Add **ambicuity/New-Grad-Jobs** as the only next aggregator, subject to the
cross-source dedup work in ticket 09.  In the 2026-07-30 snapshot it contributes
about **1,376 apparently distinct Records** beyond Simplify (95.5% of its 1,441
rows), has direct employer/ATS URLs, and has strong location and date coverage.
It is the one candidate with a large, independently sourced marginal supply.

Do **not** add ApplyGuy or ForgeApply now.  ApplyGuy has usable direct destination
URLs, but about 42% of its small feed already matches Simplify; its estimated 126
unique rows do not justify another cron source yet.  ForgeApply's estimated 205
unique non-intern rows are interesting, but its API supplies a ForgeApply redirect
rather than the employer URL: it is a portability and dedup risk.  Reconsider only
if its API adds a verified destination URL.  Keep Simplify as baseline, but it is
not enough diversity by itself.

These are measurements of a time-stamped snapshot, not claims that jobs remain
open; a source is allowed to contain Cross-posts and stale listings.  “Unique” below
means **not matched by the stated conservative comparison**, not a proof that no
other source has the same real-world requisition.

## Sources and snapshot provenance

All URLs below are first-party repository artifacts or the service’s public API.
Artifacts were downloaded on 2026-07-30 into a disposable local directory; no
candidate source was inferred from a README table.

| Feed | Authoritative structured endpoint | Snapshot / freshness evidence | Shape useful to this project |
| --- | --- | --- | --- |
| Simplify (baseline) | [raw `listings.json`](https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json) ([repository](https://github.com/SimplifyJobs/New-Grad-Positions)) | 17,741 total; 2,742 `active && is_visible` at measurement. The current file, rather than a README count, is the count authority. | Array; `id`, `company_name`, `title`, `locations[]`, `url`, `date_posted`, `date_updated`, `active`, `is_visible`, `sponsorship`, `degrees`. |
| ambicuity | [current raw `docs/jobs.json`](https://raw.githubusercontent.com/ambicuity/New-Grad-Jobs/main/docs/jobs.json) ([repository](https://github.com/ambicuity/New-Grad-Jobs)) | `meta.generated_at` was `2026-07-30T18:25:32.112519+00:00`; 1,441 rows. This corrects the old root [`jobs.json`](https://raw.githubusercontent.com/ambicuity/New-Grad-Jobs/main/jobs.json), which was stale (2026-03-06). Inspect the [main-branch commit history](https://github.com/ambicuity/New-Grad-Jobs/commits/main/) when implementing rather than hard-coding an assumed cadence. | Object `{meta, jobs}`; job has stable string `id`, company/title/location, direct `url`, ISO `posted_at`, `source`, category/tier, flags, `is_closed`, plain and HTML description. |
| ApplyGuy | [raw `data/new-grad-jobs.json`](https://raw.githubusercontent.com/ApplyGuy/2027-New-Grad-Jobs/main/data/new-grad-jobs.json) ([repository](https://github.com/ApplyGuy/2027-New-Grad-Jobs)) | 217 rows; top-level `updatedAt` was `2026-07-30T19:15:35.670Z`. Inspect [main commits](https://github.com/ApplyGuy/2027-New-Grad-Jobs/commits/main/) for operational freshness. | Object `{updatedAt, jobs}`; `id`, company/title/location, eligibility and match kind, date-only `posted`, UI `url`, and, importantly, direct employer `listingUrl`. |
| ForgeApply | [public early-career API](https://forgeapply.com/api/public/early-career) | API returned 797 rows; `generated_at` was `2026-07-30T19:29:10.042Z`. Its own public feed is the freshness authority. | Object `{count, generated_at, jobs}`; title/company/location/salary/ISO `posted_at`, but `url` is a `forgeapply.com/j/...` redirect, not the employer listing. |

### ambicuity source mix and data quality

The snapshot’s `meta.total_jobs` equals 1,441.  Grouping `jobs[].source` produced
Greenhouse 1,015, JobSpy (Indeed) 167, Workday 132, Ashby 116, and Lever 11.  This
is materially independent *collection* from Simplify, although it can still find the
same company posting.  Its direct `url`, closed flag, ISO timestamp, and text
description map cleanly to a Record.  Its named source says nothing about whether a
specific URL is still valid, so fetch failures must be handled source-scoped (Closed,
not deletion) as required by [CONTEXT.md](../../../CONTEXT.md).

## Reproducible overlap measurement

### Baseline and normalization

The comparison used the downloaded current Simplify array (17,741 total, 2,742 active
and visible) and each complete candidate snapshot.  For every row, normalize company,
title, and location by lowercasing; replace punctuation with spaces; collapse
whitespace; and normalize known ATS URL forms to their external requisition ID when
one can be extracted.  Do **not** treat shared company alone, a title alone, or a
redirect URL as a Cross-post.

1. Match equal external requisition IDs where both sides expose them.
2. For remaining rows, group by normalized company, require compatible normalized
   locations, and compare normalized titles. The measurement used exact titles for
   ambicuity and a token-Jaccard threshold of 0.75 for the smaller ApplyGuy and
   ForgeApply estimates.
3. ForgeApply hides the destination URL, so its fuzzy company/title/location result
   is only an estimate; it is deliberately not strong enough to be production dedup.

This is reproducible with `jq` (count/filter/schema) plus a small normalizer following
the three rules above.  Re-run it against pinned downloads and save the download time,
file SHA-256, source commit SHA, row counts, and comparison code with an implementation
PR.  The raw branch URLs intentionally move; the linked main-branch commit pages are
the source for recording those SHAs.

| Candidate | Population compared | Matched Simplify Cross-post candidates | Apparently unique | Interpretation |
| --- | ---: | ---: | ---: | --- |
| ambicuity | 1,441 all rows | ~65 (4.5%) | ~1,376 | Large marginal coverage; best next feed. |
| ApplyGuy | 217 all rows | ~91 (41.9%) | ~126 | Some marginal value, but far below ambicuity. |
| ForgeApply | 214 rows after its non-intern title rule | ~9 (4.2%) | ~205 | Low measured overlap but lowest confidence because only redirect URLs are exposed. |

The exact-match stages can create **false negatives** when one feed abbreviates a
company/location, one source has a multi-location role, titles include a team suffix,
or an ATS external ID is absent/different.  They can create **false positives** when
a company genuinely has two requisitions with the same title and location.  The
ForgeApply fuzzy estimate has both risks amplified.  Therefore use the numbers to rank
marginal supply, never as licence to collapse records automatically; ticket 09 must
preserve distinct requisitions and only collapse genuine Cross-posts.

## Bay Area relevance

Applied the current `BAY_TERMS`/bare-Remote policy from
[CONTEXT.md](../../../CONTEXT.md) to each snapshot’s location field (for Simplify,
the joined `locations[]`).  Before the explicit foreign-remote exclusion is applied,
the simple text screen found: Simplify active+visible 427, ambicuity 537, ApplyGuy 38,
and ForgeApply non-intern 57.  Those counts are **upper bounds**, not candidate counts:
they include every seniority, title family, and potentially foreign-qualified Remote
row.  Still, ambicuity’s count confirms practical Bay Area/Remote relevance; all three
candidates provide a location field sufficient to apply the project’s policy.

## Rejections and mirror traps

### SuryaHarikrishnan/internship-tracker — reject: wrong scope and upstream overlap

The first-party [JSON artifact](https://raw.githubusercontent.com/SuryaHarikrishnan/internship-tracker/master/data/listings.json)
([repository](https://github.com/SuryaHarikrishnan/internship-tracker)) is structured
and has useful fields (`company_name`, `title`, `locations`, `date_posted`,
`date_updated`, `url`, `is_visible`, `_sources`).  But it is an **internship**
tracker, whereas this ticket seeks full-time new-grad positions.  Its
[attribution](https://github.com/SuryaHarikrishnan/internship-tracker/blob/master/ATTRIBUTION.md)
says the data are not original and identifies Simplify and vanshb03 internship
repositories as inputs.  Its [parser](https://github.com/SuryaHarikrishnan/internship-tracker/blob/master/scripts/scrape.py)
deduplicates normalized company/title/first-location rows, while its
[workflow](https://github.com/SuryaHarikrishnan/internship-tracker/blob/master/.github/workflows/refresh.yml)
runs five times daily.  That is competent downstream aggregation, not independent
new-grad supply; a failed upstream fetch can also be warned/skipped.  Reject unless
the product scope explicitly expands to internships.

### SpeedyApply and README lists — reject as feed inputs

[SpeedyApply’s public repository](https://github.com/speedyapply/2027-SWE-College-Jobs)
is updated frequently, but it commits Markdown tables rather than a JSON/CSV artifact.
Its first-party
[`queries.ts`](https://github.com/speedyapply/2027-SWE-College-Jobs/blob/main/.github/scripts/src/queries.ts)
reads a Supabase RPC and
[`supabase.ts`](https://github.com/speedyapply/2027-SWE-College-Jobs/blob/main/.github/scripts/src/supabase.ts)
requires `SUPABASE_URL` and `SUPABASE_KEY`; neither a public endpoint nor credentials
are published. Treat it as a discovery list, not a fetchable structured feed.

Likewise, public lists presented only as repository README/Markdown tables require
brittle parser maintenance and often reuse the same community submissions.  Examples
to treat as a discovery-only mirror trap are [Jobright’s New-Grad-Jobs repository](https://github.com/jobright-ai/2025-New-Grad-Jobs)
and [Zapply’s new-grad list](https://github.com/zapplyjobs/new-grad-jobs).  A README
row is not eligible for ingestion until a first-party JSON/CSV/API endpoint and its
provenance are found.  This prevents a mirror from being mistaken for independent
supply.

## Ranking and implementation gate

1. **ambicuity — recommend.** ~1,376 apparent additions, direct employer URLs,
   complete locations and dates. Fetch `docs/jobs.json`, map `is_closed` to source
   state, retain its source and external ID, and run dedup before notifying.
2. **ForgeApply — defer.** ~205 estimated additions, but redirect-only URLs mean the
   actual external ID cannot support robust Cross-post detection or durable links.
3. **ApplyGuy — defer.** ~126 apparent additions; good `listingUrl`, but enough overlap
   with Simplify that it is a poor next use of cron/storage budget.
4. **Surya tracker and README-only lists — reject.** Scope mismatch or no durable
   structured/provenanced artifact.

Before merging an ambicuity fetcher, pin a new snapshot and repeat the table above;
test its endpoint failure, `is_closed` transitions, URL preservation, and known
Cross-posts.  A changed commit/hash, schema, or a sharp overlap swing is a reason to
re-review rather than silently ingest a different feed.
