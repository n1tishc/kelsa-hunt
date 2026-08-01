# Map: Kelsa-hunt as one coherent tool

<!-- wayfinder:map -->

## Destination

`kelsa-hunt` settled as a single coherent system: a committed store whose shape is
deliberately chosen, broad source coverage across companies/ATS platforms/aggregators,
Discord alerts that are verified to arrive, and a public HTML dashboard over everything
the tool has ever seen — with application history staying private. Done when every
decision below is made and someone can go build it without asking another question.

## Notes

**Domain:** job-alerting automation. Python stdlib only, GitHub Actions, no server.

**Skills every session should consult:** `/grilling`, `/domain-modeling`. Use
`/prototype` for the dashboard ticket, `/research` for source-survey tickets.

**Read first:** `CONTEXT.md` (the domain language — Record, Score, Candidate, Closed,
Cross-post) and `docs/adr/0001-repo-public-annotations-private.md`. Both encode
decisions already locked; don't re-litigate them without cause.

**Standing constraints for this effort:**

- **Repo stays public.** ADR-0001 — it's the only zero-cost option at this cron rate.
  Anything that requires a private repo is out of scope.
- **Application history stays private.** `applied_at` / `hidden` live in the gitignored
  `annotations.json` and are never committed. Decided this session: the public dashboard
  renders **job data only** — never applied state.
- **Storage is recall-first, notification is precision-first.** Every Record is kept
  forever; only Score ≥5 pings Discord. Re-scoring is retroactive, so any classifier or
  threshold change can be tested against all ~13k historical records for free via
  `query --all --max-age 0 --min-score N`.
- **The Discord silence is diagnosed — don't re-derive it.** Measured 2026-07-30: the
  `--seed` run stamped all 23 then-current matches `notified_at` without sending (that is
  what seeding does, per README step 4 — all 23 share the single timestamp
  `1785401837`). Every run since has succeeded with the `DISCORD_WEBHOOK` secret present
  and produced **zero** rows clearing Score ≥5 + Bay Area + ≤21 days. The silence is
  correct behaviour, not a broken webhook. What remains unproven is that `post_discord`
  can deliver *at all* — it has never made a successful call — which is the whole of
  **Verify Discord delivery end-to-end**.
- **The store is the binding constraint.** Measured 2026-07-30: `jobs.json` is 6.5 MB,
  rewritten ~21,300 lines per run because `last_seen` updates on nearly every record.
  Repo hit 10.7 MiB of loose objects after 7 bot commits. More sources, an Excel export,
  and a dashboard are all additional copies or additional churn on top of this. Nearly
  everything downstream waits on **Decide the committed store's shape**.

**Blocking convention:** this tracker has no native dependency edges. Each ticket names
its blockers in a `## Blocked by` section. A ticket is on the frontier when every ticket
it names is closed and it has no `## Claimed by` line.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [Survey which ATS platforms expose usable public job APIs](tickets/05-ats-platform-survey.md)
  — SmartRecruiters, Workable, and Recruitee fit the GET/JSON boundary; Workday does not.
- [Assemble the target company list and its board slugs](tickets/06-target-company-list.md)
  — 105 current-fetcher boards are live; one same-day migration was removed.
- [Find aggregator feeds worth adding beyond Simplify](tickets/07-aggregator-feeds.md)
  — ambicuity is the only recommended next feed and waits on Cross-post identity.
- [Decide the committed store's shape](tickets/01-committed-store-shape.md)
  — keep one stable `jobs.json` Canonical Store; remove heartbeat churn and derive other views.
- [Set the run-time and Actions-minutes budget](tickets/08-runtime-and-minutes-budget.md)
  — fetch every source with eight workers; use a best-effort 30-minute/2-hour cadence.
- [Verify Discord delivery end-to-end](tickets/02-verify-discord-delivery.md)
  — one scratch-store embed was accepted by Discord and visibly arrived.
- [Prototype the dashboard and decide how it gets its data](tickets/10-dashboard-shape.md)
  — ship a simple US-only spreadsheet ledger from an uncommitted Pages deployment artifact.
- [Decide whether an Excel export survives the dashboard](tickets/11-does-excel-survive.md)
  — cut Excel; the dashboard owns the read-only archive, while editable tracking stays private.
- [Re-tune the notification threshold and age gate against full history](tickets/04-threshold-and-age-gate.md)
  — keep Score 5+, the 21-day Freshness Timestamp gate, MTS +5, and the L4+/E4+ hard reject.
- [Decide how a Record is identified across many sources](tickets/09-dedup-across-many-sources.md)
  — collapse only proven platform-scoped Opening Identities; uncertain Records stay distinct.
- [Set notification UX at expanded source volume](tickets/13-notification-ux-at-expanded-volume.md)
  — use per-scan rich alerts for up to five Candidates, then lossless paged digests without a daily cap.
- [Set the Canonical Store growth guardrail](tickets/12-canonical-store-growth-guardrail.md)
  — keep one file below 25 MiB/2 seconds/250 MiB Git, then migrate reversibly to 16 stable UID shards.

## Not yet specified

In-scope fog; graduates into tickets as the frontier advances.

- **Day-to-day applied-tracking workflow.** `applied <needle>` is a CLI command against
  a gitignored file that doesn't survive a fresh clone. Once the dashboard exists, how
  you actually mark things applied is likely to change — but the shape depends on what
  the dashboard turns out to be.
- **Whether historical analytics is worth surfacing.** The dashboard prototype tested
  this as variant C and deliberately left it out of the first version. Reconsider only
  if using the spreadsheet ledger exposes a concrete analytical need.
- **Sponsorship filtering.** Simplify supplies a `sponsorship` field that is stored and
  never read. Whether it should gate or annotate matches is unclear until we know how
  much noise it would actually remove.

## Out of scope

Ruled beyond the destination. Never graduates; returns only if the destination is redrawn.

- **Making the repo private.** Reverses ADR-0001 and puts the workflow back on the
  2,000-minute free tier, which the ADR estimates this cron rate already exceeds.
- **Rendering applied/hidden state on the public dashboard.** Decided this session:
  public page shows job data only. The "public shell, private overlay" variant was
  considered and set aside as complexity without a clear win.
- **The conversation knowledge graph.** Requested alongside these features, but it's
  tooling for preserving *session context* (`/graphify`), not a decision on the route to
  the tool. Handled separately, outside this map.
