# Second source batch, and the real Actions timing that resolves ticket 22's open risk

<!-- wayfinder:task -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

Requested directly (not charted): find more high-ROI startups and notable employers to
add to `sources.json`, continuing
[the fall-cycle expansion](22-fall-cycle-source-expansion.md) and
[the Wellfound/YC reframe](18-wellfound-yc-source-survey.md) — mine more candidate
companies via prior knowledge, verify each live, add the ones that check out.

This ticket also closes the open risk ticket 22 explicitly left unsettled: an observed
end-to-end Actions wall-clock for the unsharded scan.

## What was found: 19 net-new verified slugs

Same verification discipline as tickets 18/19/22 — observed live, non-empty, correct
company, engineering-track titles present (not sales/ops-only), no cross-platform
collision:

| Platform | Slug | Jobs | Eng-track share | Note |
|---|---|---:|---:|---|
| greenhouse | cresta | 96 | 47/96 | |
| greenhouse | observeai | 20 | 10/20 | Observe.AI |
| greenhouse | assemblyai | 9 | 5/9 | small board, high eng share |
| greenhouse | roblox | 224 | 148/224 | PhD-early-career ML titles present |
| greenhouse | discord | 48 | 31/48 | |
| greenhouse | clickhouse | 172 | 123/172 | includes a UK-remote eng req |
| greenhouse | chainguard | 82 | 32/82 | |
| greenhouse | calendly | 11 | 6/11 | |
| greenhouse | speechify | 1289 | 1181/1289 | see hazard note below |
| greenhouse | otter | 26 | 15/26 | Otter.ai |
| greenhouse | agilityrobotics | 59 | 32/59 | humanoid robotics |
| greenhouse | truveta | 39 | 25/39 | health data |
| greenhouse | komodohealth | 35 | 12/35 | health data |
| ashby | render | 35 | 20/35 | |
| ashby | railway | 8 | 8/8 | 100% engineering |
| ashby | airbyte | 10 | 6/10 | |
| ashby | socket | 24 | 13/24 | |
| ashby | workos | 25 | 15/25 | |
| ashby | middesk | 20 | 7/20 | |

`sources.json` inventory: 195 → 214 configured fetches (greenhouse 100→113, ashby
82→88). `growth_guardrail.duplicate_source_names` returns `{}`.

**Dropped, honoring ticket 22's prior call rather than re-litigating it:** Webflow,
Mercury, Salesloft, Honeycomb, PlanetScale — already probed and excluded last session as
thin/sales-heavy. Re-discovered independently this session via the same slug-guessing
method; not re-added.

**Dropped this round, same reason:** Netlify (0/3 eng), Descript (2/10), Codat (2/5) —
live, correct-company boards but negligible engineering-track volume. Figure (1/19 eng)
was also dropped — the live `figure` Greenhouse slug is Figure Technology Solutions
(fintech lending, Reno NV roles), not Figure AI (humanoid robotics); wrong company for
what was intended, and thin on engineering regardless. Apollo, Raycast, and Clerk
returned `200` with genuinely empty job lists (real tenants, zero current openings) —
excluded per the non-empty rule ticket 19 established; worth re-checking later since the
tenants are confirmed real.

**Hazard — Speechify's board is unusually large.** 1,289 open postings, the largest
single source in the inventory, because the company posts the same handful of role types
separately per city (e.g. "Senior Software Engineer, Windows/Desktop Applications" repeated
across dozens of cities). Verified as a real, correctly-attributed board (apply URLs on
`job-boards.greenhouse.io/speechify`), not a scraping artifact. Flagged for visibility,
not excluded — the Store is recall-first and the Expansion Gate has ample headroom (see
below), but if Speechify's board keeps growing, watch it as the first candidate to prune.

**Slug-guessing yield, for the record:** ~65 greenhouse and ~25 ashby candidate slugs
were probed this session across two rounds; 24 returned live, correct-company, non-empty
boards (roughly 27%), consistent with ticket 18's own finding that name-guessing against
undocumented ATS tenants is inherently low-yield (36 of 325 there, ~11%) — this session's
higher hit rate likely reflects targeting better-known, larger companies rather than a
better method.

## What was found: the real Actions timing answers ticket 22's open risk

Ticket 22 left one acceptance item explicitly open: "an observed end-to-end Actions
wall-clock for the (now 195-source, unsharded) scan. Watch the first few scheduled runs
after this merges." Pulled via `gh run view --log` on 2026-08-10, four completed
scheduled runs against the 195-source inventory (pre-dating this ticket's 19 additions):

| Run | `wall_seconds` | vs. 240s warning |
|---|---:|---|
| 19:14 UTC | 226.43 | under, 14s margin |
| 18:01 UTC | 241.82 | **tripped the warning** |
| 17:07 UTC | 205.61 | under |
| 16:09 UTC | 224.17 | under |

**This corrects, not confirms, the local measurement ticket 22 discarded as sandbox
noise.** The local 235s figure that originally drove the (later-reverted) shard proposal
turned out to be unreliable *as an absolute local number* — shard/unsharded reruns on the
same inventory ranged 5s to 10+ minutes locally. But the real Actions number lands in
almost exactly the same place: 205–242s against a 240s warning / 300s hard gate /
5-minute job timeout, already crossing the warning line on one of four observed runs,
*before* today's 19-source addition (195 → 214, +9.7%). Extrapolating that growth against
a number already sitting at the warning line made single-job unsharded scanning an
unacceptable risk to add 19 more sources on top of.

## Decision: re-enable the shard split

Presented to the user with the real timing data; the user chose to enable sharding now
rather than commit more sources onto a scan already brushing its budget.

`.github/workflows/alert.yml` gained a second job, `scan-shard-1`, sequential after
`scan` (`needs: scan`) so the two never push `jobs.json` concurrently:

- `scan` runs `job_alert.py scan --shard 0 --shard-count 2`, persists if changed, as before.
- `scan-shard-1` checks out `${{ github.ref }}` (picks up `scan`'s push), runs
  `--shard 1 --shard-count 2`, persists if changed, same pattern.
- `dashboard` now needs `[scan, scan-shard-1]` and triggers if **either** shard's
  `store_changed` output is `'true'` — written as
  `needs.scan.outputs.store_changed == 'true' || needs['scan-shard-1'].outputs.store_changed == 'true'`.
  Bracket notation is required for the hyphenated job id: a bare `needs.scan-shard-1`
  parses the hyphen as subtraction inside a `${{ }}` expression.
- `deploy` is unchanged (`needs: dashboard`).

`shard_sources()` and the `--shard`/`--shard-count` flags already existed
(built in ticket 22, dormant) — no `job_alert.py` changes were needed this time, only the
workflow wiring.

**Accepted, analyzed risk carried over from ticket 22's original design:** a failed git
push landing between the two shards' persist steps could theoretically produce a
duplicate notification, and only actualizes for a proven Cross-post. `scan-shard-1`
`needs: scan` (not `always()`), so a hard failure in `scan` skips `scan-shard-1` entirely
that cycle rather than risking a stale-base push — degraded delivery for one cycle, not
silent duplication.

## Acceptance

- [x] `sources.json`: 19 net-new slugs added (195 → 214 fetches), verified live,
      non-empty, correct company, engineering-track presence checked.
      `growth_guardrail.duplicate_source_names` returns `{}`.
- [x] `tests/test_source_inventory.py` updated for the new counts (113/5/88, 214 total
      fetches).
- [x] `.github/workflows/alert.yml` gains `scan-shard-1`; `dashboard`'s `if` condition
      checks both shards' `store_changed` outputs.
- [x] `README.md` updated: sharding documented as active, with the real timing numbers
      that justified it.
- [x] Full suite green: `.venv/bin/python -m unittest discover -s tests` — 142 tests, OK.
- [x] `growth_guardrail.py --baseline-ref <HEAD>` run locally: within limits — 15.3 MB
      store (33,865 Records — grown from 24,650 since ticket 22, confirming the scheduled
      workflow has been running successfully throughout), ~0.30s load/save medians, 25.8 MB
      packed Git. All well under their respective warning thresholds.
- [ ] **Not yet observed:** Actions wall-clock for each shard under the new 214-source,
      two-job split. Watch the next few scheduled runs; each shard now carries roughly
      half of 214 fetches, so per-job wall-clock should land well under 240s, but this is
      a prediction, not a measurement, until confirmed the same way ticket 22's gap was
      closed here.

## Blocked by

_(nothing — frontier)_

## Related work

- [Expand the Source Inventory for the fall new-grad cycle](22-fall-cycle-source-expansion.md)
  — the prior batch, the dropped-board list this ticket honors, and the shard-split code
  this ticket activates.
- [Fit the expanded Source Inventory to the scan-time budget](21-scan-time-budget.md) —
  originally proposed the shard mechanism; this ticket is the "real Actions run" its own
  acceptance criteria demanded before treating the split as settled.
- [Survey Wellfound and YC Work at a Startup against the GET/JSON boundary](18-wellfound-yc-source-survey.md)
  — the reframe technique (harvest companies onto existing ATS adapters) this ticket
  reuses for a second round of candidates.
