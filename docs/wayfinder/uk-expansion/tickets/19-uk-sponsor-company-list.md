# Assemble the UK sponsor-company list and verify board slugs

<!-- wayfinder:research -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

Which UK-based or UK-hiring companies that sponsor international workers run their careers
on an ATS kelsa-hunt already fetches, and what are their verified board slugs?

The charted decision made "hires internationals" a **source-selection criterion** rather
than a runtime filter — because the stored `sponsorship` field carries usable signal on only
27 of 24,650 Records, so a per-posting gate would suppress nearly every real UK role.
Sponsorship therefore shapes *which companies enter `sources.json`*, and this ticket produces
that list.

Existing supported adapters, all requiring no new code: **greenhouse**, **lever**, **ashby**,
**smartrecruiters**, **workable**, **recruitee**.

### What to determine

- **A defensible sponsor signal.** The UK Home Office publishes a *register of licensed
  sponsors (workers)*. Establish whether it is retrievable as a stable machine-readable file
  and usable as a **curation reference**. Note: it is a reference for human selection here,
  not a runtime join — the charted decision explicitly avoided automated name matching, so
  do not build one, and do not let name-normalisation difficulty block the ticket.
- **Candidate companies.** UK tech employers plausibly hiring new-grad/entry-level SWE or
  MLE and plausibly sponsoring. Reasonable starting territory: Monzo, Revolut, Wise,
  Starling Bank, Deliveroo, Octopus Energy, Improbable, Snyk, Cloudflare, Google DeepMind,
  Darktrace, Checkout.com, Cleo, GoCardless, Tide, Zopa, ClearScore, Onfido, Marshmallow,
  Multiverse. Treat this as a seed, not the answer — extend it, and cut anything that fails
  the checks below.
- **Slug verification, per company.** For each candidate: which ATS, the exact slug, and a
  read-only fetch confirming the board returns JSON with UK postings present. Ticket 06
  learned this the hard way — it found one company had migrated ATS the same day. **Report a
  slug only if you observed it return data**, and date the observation.
- **Deduplicate against the current inventory.** `sources.json` already carries 109 entries.
  Cloudflare is already under `greenhouse`; several existing entries (Databricks, Palantir,
  Sierra, Intercom, Stripe, Anthropic, GitLab) already yield the 1,405 UK Records in the
  Store. Only report **net-new** slugs, and say which candidates were dropped as already
  covered.
- **Sponsor evidence per company.** For each recommended slug, one line on why it is
  believed to hire internationals — register presence, a published graduate scheme that
  states visa sponsorship, or an explicit careers-page statement. Label
  **Documented** / **Observed <date>** / **Inference**, and do not present inference as
  documentation.
- **Leveling conventions.** Flag any recommended company whose titles use non-standard
  numeric leveling, since `CONTEXT.md` records the L4+/E4+ hard reject as validated against
  the US list only.
  [The classifier ticket](17-classify-uk-titles.md) needs this.
- **Count what you add.** Report the proposed net-new feed count so
  [the scan-time budget ticket](21-scan-time-budget.md) has a number to work with.

### Deliverable

A research file at `docs/wayfinder/uk-expansion/research/19-uk-sponsor-companies.md`, in the
style of [the target company list](../../research/06-target-company-list.md): a table of
company, ATS, verified slug, observation date, sponsor evidence with label, and a
net-new-versus-already-covered column. Do **not** edit `sources.json` — that is the
implementation step, gated on
[the scan-time budget](21-scan-time-budget.md).

## Resolution

**Closed 2026-08-01.** Findings:
[UK sponsor-company list and verified board slugs](../research/19-uk-sponsor-companies.md).

**45 net-new verified slugs** — greenhouse 15, lever 3, ashby 24, smartrecruiters 1, workable 2,
recruitee 0. Every slug was fetched read-only and observed returning JSON with ≥1 UK posting on
2026-08-01. The Home Office **register of licensed sponsors** is confirmed retrievable as a
stable CSV (142,649 rows, 2026-07-31 file) and was used exactly as intended — a human curation
reference, no automated matcher built.

**Verified independently before closing.** Counts and collisions reproduced exactly: 45 slugs,
zero collisions against all 109 existing entries per adapter, zero cross-adapter name overlap,
inventory 109 → 154. Graphcore re-probed live: 225 postings / 111 UK-marker / two Band-15
graduate titles — matches.

**Three corrections to the research file's own framing:**

1. **The per-board UK counts are on the researcher's looser segment-wise matcher, not on a
   strict country-marker test.** Verified: **Deliveroo** is reported at 185/120 UK, but under a
   country-marker-required test it yields **2**. Its Ashby tenant writes
   `London - The River Building HQ` (78 postings), `Manchester - Main Office` (21), `Swansea` (5)
   — no country marker anywhere, in the *same* format as `Dubai - Main Office` and
   `Paris - Main Office`. Its `Software Engineer, New Grad` in London is therefore **invisible**
   to today's predicate. Treat every UK count in that file as an upper bound pending
   [ticket 15](15-eligible-region-boundary.md).
2. **The "Wise `IC4` would be silently accepted" claim is overstated.** Verified:
   `IC4 Engineer` → `(False, 0, 'no entry-level signal')` — rejected, not accepted. With a
   `Bachelor's` degree tag it reaches Band **3**, which is a manual-sweep tier and never
   auto-notifies. The accurate statement: `IC4` escapes the *hard reject* that forces `L4`/`E4`
   to 0, so it can enter at Band 3 — a much milder issue than reported.
3. **The Canonical L3 false positive is real.** Verified:
   `Software Engineer - L3 Support` → `(True, 5, 'junior-level marker')`. `WEAK_POS` matches
   `l3\b`, but Canonical's "L3" is a third-line *support tier*, not a new-grad rung.
   [Ticket 17](17-classify-uk-titles.md) must handle it.

**Confirmed negative, and it is good news:** zero UK titles across all 45 boards match
`level\s*[4-9]` / `l[4-9]\b` / `e[4-9]\b`, so the `L4+/E4+` hard reject is not silently dropping
UK roles on this list. The pre-hedge ticket 17 worried about is not needed.

**Dropped:** Cloudflare (already configured); Darktrace (Workday — out of scope per ticket 05);
Revolut (HTTP 403 bot protection, not bypassed — the highest-value miss); Cleo (the live `cleo`
board is a *different company*); Google DeepMind and Snyk (0 UK postings); Starling Bank,
Checkout.com, ClearScore, Onfido (no board on any supported adapter); ~30 others for 0 UK
postings.

**Weakest rows, prune first if the list needs tightening:** Man Group and IMC Trading have **no
register row found at all**; ComplyAdvantage and Zego rest on an **Inference** brand→legal-entity
link. Their visible London graduate hiring is *relevance* evidence, not *sponsor* evidence.

**Bonus — partially clears the map's EU-tenant fog:** 4 of 15 Greenhouse boards sit on
`job-boards.eu.greenhouse.io` yet read fine through the standard endpoint with no fetcher change.
Three boards return apply URLs on the company's own domain with no `greenhouse.io` host, which
matters for Opening Identity extraction.

## Blocked by

_(nothing — frontier)_

## Related work

- [Assemble the target company list and its board slugs](../../tickets/06-target-company-list.md)
  — the same exercise for the US; reuse its verification discipline.
- [Survey which ATS platforms expose usable public job APIs](../../tickets/05-ats-platform-survey.md)
  — the supported-adapter boundary.
- [Survey Wellfound and YC Work at a Startup](18-wellfound-yc-source-survey.md) — may hand
  this ticket a candidate slug list.
