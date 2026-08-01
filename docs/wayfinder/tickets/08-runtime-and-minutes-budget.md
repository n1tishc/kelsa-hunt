# Set the run-time and Actions-minutes budget

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

How many sources can a single run afford to fetch, at what cadence, and what happens when
one of them is slow or down?

Source expansion runs straight into a wall the current design doesn't acknowledge:

- `cmd_scan` fetches sources **strictly sequentially** with a `time.sleep(0.3)` between
  each. At 100+ sources that's minutes of wall time before any filtering happens.
- The workflow sets `timeout-minutes: 10`. A slow platform can blow the whole run.
- The cron is already not firing as configured. **Measured** on 2026-07-30 via
  `gh run list`: 7 runs exist for the whole day, against ~40 expected from
  `*/15 14-23 * * 1-5` alone. Only four (15:46, 15:50, 17:17, 17:23 UTC) fall inside the
  `14-23` window. The missing runs were **never created** — this is not the workflow
  running and skipping its commit via `git diff --staged --quiet ||`, since no run records
  exist at all. The widely-reported cause is GitHub deprioritizing short schedules on
  scheduled workflows, but that mechanism is **inferred, not confirmed here** — confirm it
  before designing around it. **Decide whether to fight this or accept a ~2-hour effective
  cadence and delete the `*/15` cron as misleading.**
- `concurrency: cancel-in-progress: false` means a long run delays the next rather than
  being replaced. Longer runs make this compound.

Things to settle: parallel vs. sequential fetching; per-source timeout and failure
isolation (`mark_closed` already correctly skips sources that failed — confirm that
survives); whether all sources need fetching every run or can be tiered by how often they
change; and the real cadence to target.

Bring measurements — time an actual scan at the proposed source count rather than
estimating. ADR-0001's minutes figures are explicitly labelled estimates, never measured;
this is the ticket that fixes that.

## Blocked by

- [Survey which ATS platforms expose usable public job APIs](05-ats-platform-survey.md)
- [Assemble the target company list and its board slugs](06-target-company-list.md)
- [Find aggregator feeds worth adding beyond Simplify](07-aggregator-feeds.md)
- [Decide the committed store's shape](01-committed-store-shape.md) — per-run commit cost
  is part of the budget.

## Resolution

Resolved with the user on 2026-07-30.

### Measured basis

- Ten scheduled runs observed that day completed in 15–40 seconds: 21-second median,
  21.9-second mean.
- A scratch scan of the proposed inventory using the current sequential implementation
  completed in 61.45 seconds. The fixed `0.3s` sleeps alone account for roughly 32
  seconds at this source count.
- The same 107 Source Fetches (105 boards, Simplify, and the now-rejected LendingClub
  probe) completed in 4.52 seconds with eight workers: 0.21-second median source
  latency, 0.83-second p95, and 2.03-second maximum.
- LendingClub's Greenhouse board returned 404 despite verifying earlier that day. It
  was removed from the target inventory, directly validating failure isolation and
  source-health requirements.
- [GitHub documents scheduled workflows as best-effort](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule):
  high load can delay runs or drop queued jobs, especially near the start of an hour.
  The schedule must avoid `:00` and must not promise exact delivery.

### Fetch and failure budget

- Fetch all enabled sources on every scan; do not introduce source tiers while the
  complete measured fetch stage remains this small.
- Use eight global workers and permit at most four simultaneous requests to the same
  host. Remove the artificial inter-source sleeps.
- Give each request 10 seconds. Retry once with a short randomized backoff for
  timeouts, HTTP 429, and 5xx responses; do not retry other 4xx responses.
- Isolate failures. A failed, malformed, or unhealthy Source Fetch contributes no
  closure evidence and never prevents healthy sources from completing.
- If a previously non-empty source returns a valid but empty snapshot, retry once and
  then flag it for manual verification. Do not mark its Records Closed or activate a
  newly configured empty source automatically.

### Cadence and workflow envelope

- Run every 30 minutes during weekday Bay Area working hours and every two hours
  otherwise. Use off-hour minutes such as `:17` and `:47`, not the start of the hour.
- Treat the schedule as best-effort and do not add an external scheduler.
- Target normal p95 workflow completion under 60 seconds; set a five-minute hard
  workflow timeout.
- Keep `concurrency.cancel-in-progress: false`: a started scan finishes rather than
  risking interruption between notification delivery and state persistence.

### Capacity

- Initial capacity is 105 verified direct boards plus Simplify. Add
  `ambicuity/New-Grad-Jobs` only after Cross-post identity is settled.
- The design budget is 150 configured sources, approximately 690 scheduled runs per
  month, and an operational ceiling of 1,000 runner-minutes per month. The repository
  remains public, so this is an operational guardrail rather than a billing forecast.
- Reopen this decision when either 150 sources or 1,000 monthly runner-minutes is
  crossed, or when measured normal-run p95 exceeds 60 seconds.
