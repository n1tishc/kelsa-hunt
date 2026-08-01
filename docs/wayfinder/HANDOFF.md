# Handoff — 2026-07-30

Session state for whoever picks this up next. Read [map.md](map.md) first for the
actual destination/decisions; this file is just "what happened and what's next,"
not part of the wayfinder artifact set itself. Delete or archive it once its
contents are stale.

## What's done

- **Discord silence diagnosed.** Not a bug — see the Notes section of `map.md`.
  Don't re-derive it.
- **Cron reliability measured, not assumed.** Ticket
  [08](tickets/08-runtime-and-minutes-budget.md) now states the measured
  `gh run list` numbers instead of an inferred claim about GitHub deprioritizing
  short schedules.
- **Knowledge graph built** over `docs/wayfinder/` via `/graphify` — outputs in
  `graphify-out/` (`graph.html` to open in a browser, `GRAPH_REPORT.md` for the
  audit, `graph.json` for machine queries). Its last build had 34 nodes, 66 edges,
  5 communities, and health OK, but it now predates the completed 05–07 research
  and should be regenerated before treating its counts/edges as current. This is
  separate from the wayfinder map itself (see map.md's Out of scope section).
- **Frontier research tickets 05, 06, and 07 completed.**
  - [05](research/05-ats-platform-survey.md) recommends SmartRecruiters, Workable,
    and Recruitee; Workday remains outside the GET-only boundary.
  - [06](research/06-target-company-list.md) now verifies 105 boards the current
    fetchers can consume and proposes 93 net additions, not yet applied. LendingClub
    was removed after its board returned 404 during the runtime benchmark.
  - [07](research/07-aggregator-feeds.md) replaces the earlier guessed overlap with
    a real snapshot comparison and recommends only `ambicuity/New-Grad-Jobs`, after
    ticket 09.
- **[Decide the committed store's shape](tickets/01-committed-store-shape.md)
  resolved.** Keep one `jobs.json` Canonical Store, remove `last_seen`, suppress
  no-op metadata commits, and derive dashboard/export artifacts. The measured
  post-expansion projection is roughly 31,765 Records / 15.2 MB.
- **`docs/wayfinder/` and `graphify-out/` are both untracked** (`git status`
  confirms) — nothing has been committed. Ask before committing; not yet requested.
- **[Dashboard shape and data path](tickets/10-dashboard-shape.md) resolved.** Use
  variant A's simple spreadsheet ledger. It defaults to open, explicitly US-eligible
  Records at Score 3+, while complete history and all Scores remain filterable. Actions
  generates the compact JSON and page as an uncommitted Pages deployment artifact only
  after meaningful Canonical Store changes.
- **The location boundary changed deliberately.** Bare `Remote` is no longer assumed
  domestic. Every visible view and notification must require explicit US evidence;
  mixed-location Records may qualify but expose only US locations. The prototype applies
  this rule; production enforcement is tracked in
  [ticket 14](tickets/14-enforce-us-location-eligibility.md).
- **[Excel ticket 11](tickets/11-does-excel-survive.md) resolved: cut it.** The dashboard
  completely covers the requested read-only searchable record. Editable notes or
  application tracking would be a separate private workflow, not an export.

## What's in progress / blocked

- **[Set the run-time and Actions-minutes budget](tickets/08-runtime-and-minutes-budget.md)
  resolved.** Fetch every source with eight workers, a 10-second request timeout and
  isolated retry policy; use a best-effort 30-minute workday / two-hour otherwise
  cadence. Capacity is 150 sources and 1,000 runner-minutes/month.
- **[Verify Discord delivery end-to-end](tickets/02-verify-discord-delivery.md)
  resolved.** Discord accepted exactly one scratch-store embed with HTTP 204 and the
  user confirmed that it visibly arrived. The production store was untouched.
- **Ticket 09 is not yet on the frontier.** Ticket 07 is resolved, but
  [ticket 03](tickets/03-fix-notification-loss.md) still blocks the Cross-post
  identity decision.
- **[Strict-US ticket 14](tickets/14-enforce-us-location-eligibility.md) is open.**
  Production still uses the old permissive remote predicate even though `CONTEXT.md`
  now records the replacement policy.
- No source expansion has been applied to `sources.json`, and no aggregator fetcher
  has been implemented. The research results are decision inputs, not code changes.

## Suggested next steps

1. Implement the shared strict-US predicate in
   [ticket 14](tickets/14-enforce-us-location-eligibility.md), then reuse it for both
   Candidate selection and dashboard derivation.
2. If the user approves the already-identified fixes, implement and regression-test
   [ticket 03](tickets/03-fix-notification-loss.md). That unlocks
   [ticket 09](tickets/09-dedup-across-many-sources.md).
3. **Standing open items still awaiting the user:**
   - Whether to fix the two silent-notification-loss bugs now (ticket
     [03](tickets/03-fix-notification-loss.md)) — offered, no go-ahead yet.
   - Whether to commit `docs/wayfinder/` and `graphify-out/` to git.
