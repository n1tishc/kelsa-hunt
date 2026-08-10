# Map: UK roles alongside US in kelsa-hunt

<!-- wayfinder:map -->

Charted 2026-08-01. Successor effort to
[Map: Kelsa-hunt as one coherent tool](../map.md), which closed the same day with its
destination reached. That map is **archived**; this one is live.

## Destination

`kelsa-hunt` is region-aware and UK roles are live. The locked US-only eligibility
boundary is replaced by an **Eligible Region** concept spanning US and UK; the public
ledger shows UK Records; UK Candidates in major UK cities (or UK-remote) reach Discord;
`sources.json` is curated toward UK companies that hire internationals; the test suite is
green.

This map **carries execution** — see Notes. It is not done when the decisions are made;
it is done when UK roles arrive in Discord.

## Notes

**Domain:** job-alerting automation. Python stdlib only, GitHub Actions, no server.

**This effort overrides Wayfinder's plan-only default.** Tickets carry through to working
code and passing tests, matching how the predecessor map ran.

**Skills every session should consult:** `/grilling`, `/domain-modeling`. Use
`/prototype` for the presentation ticket, `/research` for the source-survey tickets.

**Read first:** `CONTEXT.md` (Record, Score, Candidate, Closed, Cross-post, US
eligibility boundary, Bay Area), [`../map.md`](../map.md) for the 14 settled decisions
this effort builds on, and
[`docs/adr/0001-repo-public-annotations-private.md`](../../adr/0001-repo-public-annotations-private.md).

**Tracker layout:** this effort lives in `docs/wayfinder/uk-expansion/`, a sibling of the
archived effort, so the old map's relative ticket links stay valid. Ticket numbering
continues from the predecessor's 14 so the project keeps one chronological decision trail.

**Blocking convention (inherited):** this tracker has no native dependency edges. Each
ticket names its blockers in a `## Blocked by` section. A ticket is on the frontier when
every ticket it names is closed and it has no `## Claimed by` line.

**Running the tests:** `pytest` is **not** installed in `.venv`. The suite is `unittest` —
`.venv/bin/python -m unittest discover -s tests` (verified 2026-08-01: `Ran 90 tests … OK`).

**Shell note:** a bare `ls` exits 1 with no output in this environment (a command-rewrite hook).
Use `/bin/ls`, or the file tools.

### Decisions made while charting

These came out of the destination grilling and are not tickets — they are the premises
every ticket below assumes.

- **One region-aware tool, not a parallel UK lane.** `CONTEXT.md`'s *US eligibility
  boundary* becomes *Eligible Region*. One Store, one classifier, one ledger, one Discord
  feed, with region carried on every Derived View. A forked `strict_uk_record()` beside
  `strict_us_record()` was considered and rejected as two things that will drift.
- **"Hires internationals" is source curation, not a filter.** Measured: the stored
  `sponsorship` field carries usable signal on **27 of 24,650 Records** (`Other` 10,244,
  missing 12,799, blank 1,472, "Offers Sponsorship" 27, "Does Not Offer Sponsorship" 26).
  A per-posting gate would suppress nearly every real UK role. So sponsorship shapes
  **which companies enter `sources.json`** and never suppresses a Record at query time.
  Recall-first storage and never-suppress notification both survive intact.
- **UK mirrors the US two-tier shape.** Whole UK is *visible* (dashboard, query, export);
  major UK cities plus UK-remote is what *notifies* — exactly the role `BAY_TERMS` and
  `is_bay_area()` play today. "Major cities for now" is therefore a data change, not a
  design change.
- **The classifier bends to UK wording.** `Graduate <eng role>` is the UK's exact
  equivalent of `New Grad <eng role>` and is promoted to Score Band 10; `ROLE_MATCH` gains
  UK vocabulary so grad schemes stop failing as "not an eng/ML role". Accepted cost: new
  Band 5 noise from non-engineering grad schemes.

### Measurements taken while charting

Recorded here so no resolving session re-derives them.

- **1,790** Records match a loose UK city/country regex; **1,405** match when an explicit
  UK country marker is required. The **385** delta is dominated by bare `London`
  (192 Records) and is the substance of
  [Define the Eligible Region boundary](tickets/15-eligible-region-boundary.md).
- The loose sweep wrongly caught `Cambridge, MA` (34), `Birmingham, AL` (17),
  `Brighton, CO - US` (17) — US/UK city-name collisions are live in the data.
- UK Records by source: Simplify 968, Greenhouse 573, Ashby 196, Lever 39, Ambicuity 14.
  Top companies: Databricks 51, Palantir 43, Sierra 41, Intercom 40, Stripe 37,
  Anthropic 36, GitLab 36.
- UK location strings: `London, UK` 469, `London` 192, `London, United Kingdom` 148,
  `London, England` 70, `United Kingdom` 45, Edinburgh 37, Manchester 29, Belfast 23,
  Leeds 19, Cambridge 17, Bristol 17, Newcastle 15, Birmingham 13, Glasgow 12, Cardiff 9,
  plus 78 across `Remote - United Kingdom` / `Remote in UK` / `Remote - UK` /
  `Remote, United Kingdom`.
- **No backfill flood.** Opening the region predicate makes **26** UK Records notify
  immediately (Score ≥5, open, inside the 21-day Freshness gate; 1 already notified). One
  paged digest, already lossless. This needs no ticket.
- Score distribution over the 1,405 confirmed-UK Records: band 15 → 2, band 10 → 25,
  band 5 → 250, band 3 → 93, rejected → 1,035. Top rejection reasons: "not an eng/ML
  role" 492, "senior-level title" 338, "no entry-level signal" 194.
- **Expansion Gate is not binding.** Store is 11,068,104 bytes (10.6 MiB) against a 20 MiB
  warning / 25 MiB hard gate; load/save median ~0.21s against a 1.6s warning / 2.0s hard
  gate. The unmeasured risk is *scan wall-clock*, which `growth_guardrail.py` never looks
  at — see [Fit the expanded Source Inventory to the scan-time budget](tickets/21-scan-time-budget.md).

### Standing constraints inherited from the archived map

- **Repo stays public** (ADR-0001). Anything requiring a private repo is out of scope.
- **Application history stays private.** `annotations.json` is gitignored and never
  committed; the public ledger renders job data only.
- **Storage is recall-first, notification is precision-first.** Every Record is kept
  forever, and Score is computed at query time so re-scoring is retroactive.
  **Inherited claim corrected 2026-08-01:** `CONTEXT.md` and the archived map say a
  classifier change can be tested "against all ~24.6k historical Records for free via
  `query --all --max-age 0 --min-score N`". It cannot. `cmd_query` reads
  `Store.candidates()`, which applies `strict_us_record()` *and* `is_bay_area()` *and*
  `dedup()` first — that command returns **229** matches, not 24,650 (observed). An
  all-history sweep has to call `classify()` directly over `jobs.json`. See
  [Make classify() UK-title-aware](tickets/17-classify-uk-titles.md) for both instruments.
- **Discord delivery is verified and loss is visible.** Accepted pages are checkpointed,
  rejected pages fail visibly. Do not reintroduce silent-success behavior.
- **Cross-post collapse requires proven Opening Identity.** Uncertain Records stay
  distinct; a duplicate notification beats suppressing a real requisition.
- **Automation writes state to `main`.** A global require-PR/status-check ruleset can block
  the scheduled `jobs.json` commit.
- **Pages uses the custom `job-alert` workflow**, not a Jekyll or Static HTML starter.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [Survey Wellfound and YC Work at a Startup against the GET/JSON boundary](tickets/18-wellfound-yc-source-survey.md)
  — both permanently declined for access reasons; take the reframe, which verified 36 boards on
  existing adapters at zero new adapter code.
- [Assemble the UK sponsor-company list and verify board slugs](tickets/19-uk-sponsor-company-list.md)
  — 45 net-new slugs verified live against the Home Office sponsor register; per-board UK counts
  are upper bounds until the region predicate settles.
- [Expand the Source Inventory for the fall new-grad cycle](tickets/22-fall-cycle-source-expansion.md)
  — 21 net-new big-company/AI-startup slugs (173 → 195). Local scan-timing measurements proved
  untrustworthy (5s to 10+min for the same inventory); a sharded-scan mitigation was built and
  tested but the user chose to hold it and run a single unsharded scan first, to get one real
  Actions observation before adding workflow complexity.
- [Second source batch, and the real Actions timing that resolves ticket 22's open risk](tickets/23-second-source-batch-and-real-timing.md)
  — 19 more net-new slugs (195 → 214). Real Actions runs on the pre-batch inventory landed at
  205–242s against the 240s warning, already tripping it once; the shard split ticket 22 held is
  now enabled (`scan` + `scan-shard-1`, sequential, `dashboard` triggers on either shard's change).

## Not yet specified

In-scope fog. Graduates into tickets as the frontier advances.

- **Whether the 21-day Freshness gate suits UK hiring rhythms.** UK graduate schemes
  commonly open in autumn for a start the following year, so a scheme posted six months
  ahead is both real and long past a 21-day gate. Can't be phrased sharply until
  [the classifier ticket](tickets/17-classify-uk-titles.md) reveals how many scheme-shaped
  Records actually exist and how their `posted` timestamps behave.
- **UK grad-scheme application deadlines.** A UK-specific concept with no US analogue —
  schemes close on a date rather than going stale. Whether that becomes a stored field, a
  ledger column, or nothing depends on what the sources actually supply.
- **Whether sponsorship becomes a visible ledger column.** Ruled out as a *filter* while
  charting, but once UK volume is real, surfacing whatever sponsorship string exists may
  be worth it. Revisit after UK Records are live on the ledger.
- **Cross-post identity under UK/EU ATS tenants.** *Largely cleared 2026-08-01.* Greenhouse EU
  tenants (`job-boards.eu.greenhouse.io`) read fine through the standard endpoint with **no
  fetcher change**. The sharp part — companies live on two supported platforms at once, which the
  platform-scoped [Opening Identity registry](../tickets/09-dedup-across-many-sources.md) cannot
  collapse — is now concrete (Wayve, Skyscanner) and handled in
  [the scan-time budget ticket](tickets/21-scan-time-budget.md), which owns the `sources.json`
  edit and a two-platform guard. **Residual fog:** three verified boards return apply URLs on the
  company's own domain with no `greenhouse.io` host, so `_greenhouse_identity()` cannot extract an
  id from them. That fails safe — Records stay distinct, per the settled rule that a duplicate
  beats a suppressed requisition — but it means cross-post collapse silently degrades on those
  boards. Revisit if duplicate UK notifications actually show up.
- **Region-scoped ledger URLs.** Whether the ledger needs shareable per-region views
  rather than one page with a filter — depends on what
  [the presentation ticket](tickets/20-region-presentation.md) settles.

## Out of scope

Ruled beyond this destination. Never graduates; returns only if the destination is redrawn.

- **UK grad-scheme aggregators** (Bright Network, Gradcracker, Milkround). Highest topical
  fit but not selected for this effort; they are consumer job boards and likely HTML-only,
  which fails the GET/JSON boundary that ticket 05 established.
- **UK-native ATS platforms** (Teamtailor, Pinpoint). Not selected. Workday is separately
  and permanently ruled out by
  [the ATS platform survey](../tickets/05-ats-platform-survey.md) for using
  unauthenticated POST rather than GET, despite heavy use by large UK employers.
- **Any per-posting sponsorship hard filter.** Reverses the recall-first / never-suppress
  posture and, measured against live data, would hide almost every genuine UK role.
- **Regions beyond US and UK** — EU, Canada, global-remote. The Eligible Region concept
  should not be *blocked* from extending later, but no third region is charted here.
- **Re-curating the existing 105 US company boards for sponsorship.** The same
  sponsor-curation logic arguably applies to the US list; it was not asked for, and
  half-doing it would churn a working inventory.
- **Making the repo private** (inherited: reverses ADR-0001).
- **LLM enrichment over job descriptions.** Would fix the title-only classifier limits this map
  works around, but it is a different effort with its own cost and dependency questions. Filed as
  [backlog: LLM enrichment pass](../backlog/llm-jd-enrichment.md) — do **not** pull it into the UK
  tickets.
