# Define the Eligible Region boundary

<!-- wayfinder:domain-modeling -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

What replaces the fail-closed US-only location predicate with a two-region **Eligible
Region** concept, and what does that predicate return for a location string that names a
major city with no country marker?

`CONTEXT.md`'s *US eligibility boundary* is currently an invariant: a Record is visible
only with explicit US evidence, and bare `Remote`, global, unknown, and foreign-only
locations fail closed. It is implemented across `job_alert.py` as `US_COUNTRY`,
`US_JURISDICTION_NAMES` / `_CODES`, `US_LOCALITY_ALIASES`, `KNOWN_NON_US_LOCALITIES`,
`NON_US_MARKER`, `_has_explicit_us_evidence()`, `_mixed_us_fragments()`, `us_locations()`,
and `strict_us_record()`, and it gates notifications, `query`, `export`, and the dashboard
through `Store.us_records()`.

The charted decision is one region-aware tool: `Eligible Region` replaces the US-only
boundary, `US` and `UK` are both eligible, and every Derived View carries a region.

### The hard part, already measured

Two UK sweeps over the live Store disagree by **385 Records**:

- **1,790** Records match a loose UK city-or-country regex.
- **1,405** Records match when an explicit UK country marker is required
  (`United Kingdom`, `UK`, `England`, `Scotland`, `Wales`, `Northern Ireland`).

The delta is dominated by bare **`London` — 192 Records** with no country token at all.
And the loose sweep demonstrably over-matches: it caught `Cambridge, MA` (34),
`Birmingham, AL` (17), `Brighton, CO - US` (17). London, Ontario and London, KY are real
places. So a UK city list alone cannot be evidence of UK-ness, and requiring a country
marker discards 192 probably-London Records.

For a predicate whose defining property is that ambiguity **fails closed**, this is the
decision, not a detail.

### Evidence added 2026-08-01 by the two research tickets — read this before deciding

Both research tickets independently reproduced this delta on **brand-new** sources, and the
stakes are higher than the charting sweep suggested:

- **290 openings** across the newly-verified boards hang on this single question.
  [The Wellfound/YC survey](18-wellfound-yc-source-survey.md) found **14 of 36 boards drop to
  zero UK openings** under a country-marker-required test (11 Ashby, 2 Greenhouse, 1 Lever)
  purely because those tenants omit the marker.
- **The bare-city problem is not just the bare string `London`.** A whole pattern class exists
  that the charting sweep never characterized. Deliveroo's Ashby tenant writes
  `London - The River Building HQ` (78 postings), `Manchester - Main Office` (21), `Swansea` (5)
  — and, in the identical format, `Dubai - Main Office`, `Paris - Main Office`,
  `Kuwait - Main Office`, `Hyderabad - Main Office`. So `<City> - <Office name>` must be parsed,
  and city-name matching must be substring-aware **without** admitting the foreign rows written
  the same way.
- **The concrete cost of getting this wrong.** Deliveroo is currently advertising
  `Software Engineer, New Grad` at `London - The River Building HQ` — an exact-fit role for this
  search that today's predicate cannot see. Under a country-marker-required rule Deliveroo yields
  **2** UK Records; under a bare-city rule, ~120.
- **A naive city matcher is demonstrably wrong in the other direction too.** A whole-string
  matcher scored
  `Kirkland, Washington, US; Mountain View, California, US; New York City, New York, US` as UK,
  because **"New York City" contains "York"**. Segment-wise evaluation (split on `;` / `|`, then
  require no competing US-state or other-country marker *within the same segment*) killed that
  false positive while keeping the true positive `London, UK; New York, US`. That approach is a
  reasonable starting point, not a settled answer.
- **Wayve is live on Greenhouse and Ashby at once**, and the two tenants differ *precisely* on
  this axis: the Ashby tenant emits `London, United Kingdom` (30 UK-marker rows), the Greenhouse
  tenant emits bare `London` (26 rows, 0 UK-marker), with **88 identical titles**. The same
  employer is visible or invisible depending only on which tenant is configured.

### What must be settled

- **The bare-city rule.** Does a location string naming a major UK city with no country
  marker resolve to UK, to unknown (fail closed), or to UK only when the string cannot
  also parse as a US locality (no US state name or postal code present anywhere in it)?
  Whatever is chosen, state the disposition of the 192 bare-`London` Records explicitly.
- **Collision precedence.** `US_LOCALITY_ALIASES` is derived from `BAY_TERMS`; the UK
  equivalent will contain Cambridge, Birmingham, Brighton, Newcastle — all of which are
  also US localities or carry US state codes in live data. Which region wins, and on what
  evidence?
- **The shape of the predicate.** Does `region_of(record)` return a single region, a set,
  or does `us_locations()` generalize to `region_locations(record, region)`? The existing
  contract — Derived Views expose only the *in-region* subset of locations while the
  Canonical Store retains the source's complete list — must be preserved per region.
- **Multi-region postings.** A Record located `Dublin, Ireland; London, England` (7 live
  rows) or `Hybrid - San Francisco, New York City, London, Berlin` (7 rows) is eligible in
  more than one region. Does it appear once tagged with several regions, or once per
  region? This decides the ledger's row identity.
- **Bare `Remote`.** Currently fails closed. It must keep failing closed — but
  `Remote - United Kingdom`, `Remote in UK`, `Remote - UK`, `Remote, United Kingdom`
  (78 Records combined) are explicit UK-remote and must resolve to UK.
- **`CONTEXT.md`.** Retire the *US eligibility boundary* entry and write *Eligible Region*
  in its place, without weakening the fail-closed guarantee the old entry earned.
- **Extensibility without scope creep.** A third region is out of scope for this map, but
  the concept should not be structurally hostile to one.

### Acceptance

- One shared production predicate, as
  [the US location policy ticket](../../tickets/14-enforce-us-location-eligibility.md)
  established — not a second heuristic copied beside the first.
- Table-driven tests covering both regions: country tokens, UK nations, US states and
  territories, the collision cities in both countries, source delimiters, multi-region
  postings, explicit region-remote, and ambiguous strings that must fail closed.
- The existing US test suite still passes unchanged. The US visible view must not shrink:
  it was 10,418 Records at ticket 14's resolution — a region refactor that quietly drops
  US Records is a regression.
- `jobs.json` is not rewritten by this change.

## Blocked by

_(nothing — frontier)_

## Related work

- [Enforce one strict-US location policy](../../tickets/14-enforce-us-location-eligibility.md)
  — the predicate this generalizes.
- [Set the UK notification locality tier](16-uk-notification-locality.md) — consumes this.
- [Decide how region presents in Discord and on the ledger](20-region-presentation.md).
