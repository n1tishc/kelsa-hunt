# Graph Report - docs/wayfinder  (2026-07-30)

## Corpus Check
- Corpus is ~3,519 words - fits in a single context window. You may not need a graph.

## Summary
- 34 nodes · 66 edges · 5 communities
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.88)
- Token cost: 52,514 input · 0 output

## Community Hubs (Navigation)
- Sources, Dedup, and Notification Loss
- Notification Trust Chain
- Public Surfaces and Privacy
- ATS Coverage and Fetch Reliability
- Committed Store and Run Budget

## God Nodes (most connected - your core abstractions)
1. `Map: Kelsa-hunt as one coherent tool` - 19 edges
2. `Ticket 08: Set the run-time and Actions-minutes budget` - 9 edges
3. `Ticket 04: Re-tune the notification threshold and age gate` - 6 edges
4. `Ticket 09: Decide how a Record is identified across many sources` - 6 edges
5. `Ticket 10: Prototype the dashboard and decide how it gets its data` - 6 edges
6. `Ticket 01: Decide the committed store's shape` - 5 edges
7. `Ticket 03: Fix the two ways notifications get lost silently` - 5 edges
8. `Ticket 11: Decide whether an Excel export survives the dashboard` - 5 edges
9. `The committed store (per-run committed artifact)` - 5 edges
10. `ADR-0001: repo public, annotations private` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Map: Kelsa-hunt as one coherent tool` --references--> `The committed store (per-run committed artifact)`  [EXTRACTED]
  map.md → tickets/01-committed-store-shape.md
- `Ticket 01: Decide the committed store's shape` --references--> `Map: Kelsa-hunt as one coherent tool`  [EXTRACTED]
  tickets/01-committed-store-shape.md → map.md
- `Ticket 02: Verify Discord delivery end-to-end` --references--> `Map: Kelsa-hunt as one coherent tool`  [EXTRACTED]
  tickets/02-verify-discord-delivery.md → map.md
- `Ticket 03: Fix the two ways notifications get lost silently` --references--> `Map: Kelsa-hunt as one coherent tool`  [EXTRACTED]
  tickets/03-fix-notification-loss.md → map.md
- `Ticket 05: Survey which ATS platforms expose usable public job APIs` --references--> `Map: Kelsa-hunt as one coherent tool`  [EXTRACTED]
  tickets/05-ats-platform-survey.md → map.md

## Hyperedges (group relationships)
- **Everything downstream waiting on the committed store's shape** — ticket_01_committed_store_shape, ticket_08_runtime_and_minutes_budget, ticket_10_dashboard_shape, ticket_11_does_excel_survive, concept_committed_store [EXTRACTED 1.00]
- **Notification trust chain: deliver, stop losing, then tune** — ticket_02_verify_discord_delivery, ticket_03_fix_notification_loss, ticket_04_threshold_and_age_gate, concept_discord_notification_delivery, concept_bug_post_discord_false_success, concept_bug_dedup_discards_notify_state, concept_score_threshold, concept_age_gate_21_days [EXTRACTED 1.00]

## Communities (5 total, 0 thin omitted)

### Community 0 - "Sources, Dedup, and Notification Loss"
Cohesion: 0.31
Nodes (9): Aggregator feeds and Simplify single-point-of-failure (10,215 of ~13k records), Bug 2: dedup discards notification state (notified_at stamped only on surviving uid), Bug 1: post_discord returns True after a failed non-429 send, Cross-post identity and dedup key (Greenhouse id vs. fuzzy company/title/location), Target company list and sources.json board slugs, Ticket 03: Fix the two ways notifications get lost silently, Ticket 06: Assemble the target company list and its board slugs, Ticket 07: Find aggregator feeds worth adding beyond Simplify (+1 more)

### Community 1 - "Notification Trust Chain"
Cohesion: 0.33
Nodes (9): Blocking convention: tickets name blockers in a Blocked by section, CONTEXT.md domain language (Record, Score, Candidate, Closed, Cross-post), Discord notification delivery (post_discord never made a successful call), Fog: Notification UX at higher volume, Storage is recall-first, notification is precision-first, Notification score threshold (--min-score 5, Score Bands), Map: Kelsa-hunt as one coherent tool, Ticket 02: Verify Discord delivery end-to-end (+1 more)

### Community 2 - "Public Surfaces and Privacy"
Cohesion: 0.47
Nodes (6): ADR-0001: repo public, annotations private, Excel export (vs. existing job_alert.py export to SQLite), Fog: Day-to-day applied-tracking workflow, Public HTML dashboard over the store, Ticket 10: Prototype the dashboard and decide how it gets its data, Ticket 11: Decide whether an Excel export survives the dashboard

### Community 3 - "ATS Coverage and Fetch Reliability"
Cohesion: 0.40
Nodes (5): 21-day age gate (MAX_AGE_DAYS = 21, posted semantics per source), ATS platforms with public unauthenticated board APIs, README warning: companies migrate ATS and a slug silently returns zero, Sequential source fetching in cmd_scan (time.sleep(0.3) per source), Ticket 05: Survey which ATS platforms expose usable public job APIs

### Community 4 - "Committed Store and Run Budget"
Cohesion: 0.70
Nodes (5): The committed store (per-run committed artifact), GitHub Actions cron cadence and minutes budget (*/15 not firing, timeout-minutes: 10), jobs.json size and per-run churn (6.5 MB, ~21,300 lines/run), Ticket 01: Decide the committed store's shape, Ticket 08: Set the run-time and Actions-minutes budget

## Knowledge Gaps
- **1 isolated node(s):** `Blocking convention: tickets name blockers in a Blocked by section`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Map: Kelsa-hunt as one coherent tool` connect `Notification Trust Chain` to `Sources, Dedup, and Notification Loss`, `Public Surfaces and Privacy`, `ATS Coverage and Fetch Reliability`, `Committed Store and Run Budget`?**
  _High betweenness centrality (0.645) - this node is a cross-community bridge._
- **Why does `Ticket 08: Set the run-time and Actions-minutes budget` connect `Committed Store and Run Budget` to `Sources, Dedup, and Notification Loss`, `Notification Trust Chain`, `Public Surfaces and Privacy`, `ATS Coverage and Fetch Reliability`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `Ticket 04: Re-tune the notification threshold and age gate` connect `Notification Trust Chain` to `Sources, Dedup, and Notification Loss`, `ATS Coverage and Fetch Reliability`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **What connects `Blocking convention: tickets name blockers in a Blocked by section` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._