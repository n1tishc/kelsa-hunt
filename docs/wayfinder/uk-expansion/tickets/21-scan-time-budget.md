# Fit the expanded Source Inventory to the scan-time budget

<!-- wayfinder:task -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

Does the UK-expanded Source Inventory still complete a scan inside the settled cron cadence
— and if not, what gives?

[The runtime and minutes budget ticket](../../tickets/08-runtime-and-minutes-budget.md)
settled eight concurrent workers, at most four requests per host, a ten-second request
budget, and a best-effort 30-minute weekday / 2-hour off-hours cadence across what is now
110 feeds. This ticket adds the UK slugs from
[the sponsor-company list](19-uk-sponsor-company-list.md) and whatever
[the Wellfound/YC survey](18-wellfound-yc-source-survey.md) recommends, then confirms the
result still fits.

### Measure the right thing

The **Expansion Gate is not the binding constraint here, and the existing guardrail will not
detect this risk.** Measured while charting: the Store is 11,068,104 bytes (10.6 MiB) against
a 20 MiB warning / 25 MiB hard gate, and load/save median is ~0.21s against a 1.6s warning /
2.0s hard gate. Plenty of headroom.

But `growth_guardrail.py`'s `TIMING_WARNING_SECONDS` / `TIMING_HARD_SECONDS` gate
**Store load/save duration only** — not scan wall-clock. Adding tens of boards adds *fetch*
time, which nothing currently measures. Run the guardrail and it will come back green while
telling you nothing about the actual risk.

So: measure **end-to-end `scan` wall-clock** against the 30-minute cadence, with a margin,
and report it explicitly. Also report Records added, so the Store trajectory toward 20 MiB is
known even though it is not yet a concern.

### What must be settled

- Observed scan wall-clock before and after the new feeds, on GitHub Actions rather than
  only locally — runner network behaviour is the thing being tested.
- Whether eight workers and the four-per-host cap still suit the new host mix. UK slugs on
  Greenhouse and Ashby concentrate on hosts already near the per-host cap, so added feeds may
  serialise rather than parallelise.
- Whether Actions minutes stay acceptable at the current cadence with the larger inventory,
  given ADR-0001 keeps the repo public specifically for unmetered minutes.
- Whether the guardrail should gain a scan-duration measure so this stops being a
  hand-checked property. Recommend explicitly; a "no, not worth it" is a valid answer, but
  say it rather than leaving it implied.
- If the budget does not fit: which lever moves — worker count, cadence, splitting the scan,
  or trimming the slug list. Decide, do not just report the overrun.

### Acceptance

- `sources.json` updated with the verified net-new UK slugs (this ticket owns that edit;
  ticket 19 deliberately does not).
- Observed scan wall-clock recorded with a date, from an Actions run.
- The Expansion Gate is not tripped, and its reported figures are recorded even though they
  are not the constraint.
- Full test suite green. **`pytest` is not installed** — the suite is `unittest`, run it with
  `.venv/bin/python -m unittest discover -s tests` (verified 2026-08-01: `Ran 90 tests … OK`).
- `jobs.json` growth from the first expanded scan reported.

**Explicitly NOT in this ticket's acceptance: verifying that UK Candidates arrive.** That belongs
to [ticket 15](15-eligible-region-boundary.md) and [ticket 17](17-classify-uk-titles.md). Adding
boards before the region predicate lands is **deliberately safe** — the Store is recall-first, so
every Record is kept regardless of any filter and `strict_us_record()` gates only Derived Views.
Configuring these boards early is in fact *desirable*: it accumulates UK history so that when
ticket 15 opens the predicate there is real data behind it. Do not treat the research files'
per-board UK counts as targets to reproduce; they are upper bounds measured on a looser matcher
than production uses.

## Inputs, now available — both blockers closed 2026-08-01

The two research tickets produced **overlapping** slug lists, and merging them naively is unsafe.
Computed 2026-08-01:

- [Ticket 19](19-uk-sponsor-company-list.md) proposes **45** slugs;
  [ticket 18](18-wellfound-yc-source-survey.md) proposes **36**.
- **16 were found by both** — greenhouse: `gocardless`, `graphcore`, `isomorphiclabs`, `monzo`,
  `polyai`, `sumup`, `tide`; ashby: `cohere`, `elevenlabs`, `griffin`, `improbable`,
  `multiverse`, `quantexa`, `synthesia`, `wayve`; smartrecruiters: `Wise`.
- **Union is 65 slugs**, taking the inventory to **109 → 174**. Ticket 18 contributes 20 that
  ticket 19 missed: ashby `basecamp-research`, `deepgram`, `duffel`, `encord`, `granola`,
  `legora`, `lightdash`, `lindus`, `lovable`, `n8n`, `orbital`, `poolside`, `stackone`,
  `sylvera`, `vertice`; greenhouse `faire`, `ocadogroup`, `truelayer`, `wayve`; lever `moonpig`.

**The trap, verified:** the naive union places **`wayve` on both `greenhouse` and `ashby`** —
exactly the duplicate-Record hazard both research tickets warned about, reintroduced by the merge
itself. Configure **`ashby:wayve` only** (its tenant emits the country marker; the Greenhouse
tenant emits bare `London`). That drops the union to **64 slugs → 173 entries**. `skyscanner` is
already Ashby-only in the union and needs no action.

**Add a guard, don't just fix this instance:** flag any company configured on two platforms,
since the platform-scoped Opening Identity registry cannot dedup across them.

Two more inputs from ticket 18 to fold in:

- Wise's 406 postings need **~4 extra pagination requests** beyond one-request-per-feed.
- `api.lever.co/robots.txt` asks for **`Crawl-delay: 1`**. Confirm the fetcher's per-host limit
  respects that, or say why it need not.
- Several boards hold only 3–6 openings, so a global "non-empty" health rule will produce false
  alarms. A `200` with an empty list must **never** close Records — an invariant
  [the source-fetch health work](../../tickets/08-runtime-and-minutes-budget.md) already
  established and this expansion stresses.

## Blocked by

_(nothing — frontier; both research blockers closed 2026-08-01)_

## Implementation checkpoint — 2026-08-03

- `sources.json` now contains the verified 64-slug union after the `wayve` cross-platform
  duplicate is resolved: **173 configured board entries**, or **174 fetches including the
  built-in Simplify feed**. The two feeds omitted from the first partial edit were Ashby
  `deepgram` and `granola`.
- The growth check now rejects any company slug configured on multiple platforms. This keeps
  the platform-scoped Opening Identity rule from being undermined by inventory edits.
- Each scan prints `scan metrics: wall_seconds=...` and warns at 240 seconds, leaving a
  one-minute margin inside the workflow's five-minute timeout. The existing 30-minute / two-hour
  cadence is unchanged. This is deliberately a warning, not an automatic source-expansion gate;
  a real network measurement still belongs to an Actions run.
- Local verification on this checkout: the Expansion Gate is clear with 24,650 Records,
  11,068,104 serialized bytes, load/save medians of 0.2104 and 0.2088 seconds, and 16,108,544
  packed-Git bytes. The full suite passes: `Ran 140 tests ... OK`.

The remaining acceptance item is an observed end-to-end wall-clock from GitHub Actions. It cannot
be honestly substituted with a local run because the risk being measured is runner/network
behaviour.

## Related work

- [Set the run-time and Actions-minutes budget](../../tickets/08-runtime-and-minutes-budget.md)
  — the cadence and worker settings this revalidates.
- [Set the Canonical Store growth guardrail](../../tickets/12-canonical-store-growth-guardrail.md)
  — the Expansion Gate, and the 16-way UID sharding that is its declared next response.
