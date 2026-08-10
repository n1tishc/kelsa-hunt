# Expand the Source Inventory for the fall new-grad cycle

<!-- wayfinder:task -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

Requested directly (not charted): add a meaningful batch of large-but-not-FAANG companies
and high-ROI AI-native startups ahead of the fall new-grad hiring cycle, without breaking
the scheduled scan.

This reuses two settled boundaries rather than re-litigating them:
[the ATS platform survey](../../tickets/05-ats-platform-survey.md) (GET/JSON only — no
Workday, no proprietary career sites) and
[the Wellfound/YC survey](18-wellfound-yc-source-survey.md) (both aggregators permanently
declined for access reasons; harvest their portfolio companies onto existing adapters
instead).

## What was found

**"Big companies" mostly means excluded, not new.** Google, Meta, Amazon, Apple, Microsoft,
Netflix, Nvidia, Salesforce, Uber, DoorDash, Snowflake, Atlassian, ServiceNow, and most
Workday-tenant employers were probed live on 2026-08-10 and return `404`/`401`/no
Greenhouse-Lever-Ashby-SmartRecruiters-Workable-Recruitee board — consistent with
[ticket 06](../../research/06-target-company-list.md)'s prior finding on Meta/Cisco/Apple.
This is a hard platform boundary, not a curation gap.

**Verified net-new additions (Observed 2026-08-10, all fetched read-only, non-empty,
correct company, live at time of check):**

| Platform | Slug | Jobs | Note |
|---|---|---|---|
| greenhouse | coinbase | 173 | |
| greenhouse | instacart | 115 | |
| greenhouse | dropbox | 38 | |
| greenhouse | block | 195 | Square / Cash App |
| greenhouse | airbnb | 184 | |
| greenhouse | okta | 344 | |
| greenhouse | adyen | 215 | 2 Records already clear `classify()` Score ≥5 today |
| greenhouse | gemini | 42 | |
| greenhouse | upstart | 96 | |
| ashby | replit | 88 | |
| ashby | cerebras | 123 | AI chip lab, real eng org |
| ashby | physicalintelligence | 30 | |
| ashby | thinkingmachines | 35 | Thinking Machines Lab |
| ashby | browserbase | 8 | |
| ashby | e2b | 11 | |
| ashby | attio | 42 | |
| ashby | julius | 4 | carries an explicit `Software Engineer - Product (New Grad)` title today |
| ashby | fireworks | 58 | Fireworks AI |
| ashby | hex | 30 | |
| ashby | warp | 15 | |
| ashby | substack | 12 | |

**Dropped after verification:** Squarespace, Peloton, Marqeta, Betterment, Webflow,
Mercury, Salesloft, SumoLogic, Honeycomb, PlanetScale, SingleStore, Neo4j — live boards,
but thin and sales/ops-dominated with negligible engineering-track volume. Safe Superintelligence
(`ssi` on Ashby) returns `200` with zero jobs — excluded per the non-empty rule
[ticket 19](19-uk-sponsor-company-list.md) established. `airtable`, `vercel`, `figma`,
`notion`, `deel`, `raycast` were re-probed on Ashby and correctly return empty — they're
already configured on Greenhouse/Ashby under the same slug, confirming no duplicate was
about to be introduced.

**Today's `classify()` yield from this batch is near zero** (Adyen's two Records are the
only hits), same shape as [ticket 18](18-wellfound-yc-source-survey.md)'s finding for the
UK batch. That's expected and accepted: storage is recall-first, and the stated reason for
this ticket is that the fall cycle **hasn't opened yet** at most of these employers — the
value is in watching the board before the reqs post, not in today's match count.

**`sources.json` inventory: 173 → 195** (greenhouse 91→100, ashby 70→82). Net-new count:
21 boards (9 greenhouse, 12 ashby).

## The scan budget was the real blocker, and local timing is not trustworthy here

A local `scan --dry-run` against the pre-expansion 173-source inventory measured
**235–238 seconds**, reproduced twice — against the `growth_guardrail.py` 240s warning /
300s hard gate (which is also the GitHub Actions job timeout) and the README's own stated
60-second p95 target. That is a large, surprising gap between documented budget and observed
behavior, discovered before any of the additions above were made.

**This number could not be trusted, though.** A same-inventory `--shard 0 --shard-count 2`
run (100 of 195 fetches, post-expansion) completed in 5.31s; `--shard 1` on the same
inventory took 231.31s; a third full unsharded run hung past 10 minutes and was killed. Every
individual URL in the inventory was then curled directly (bypassing `job_alert.py`'s
`urllib` client entirely) and all but two completed in under 2 seconds. The conclusion:
this sandbox's local network/DNS behavior is not representative of GitHub Actions runner
behavior, exactly as [ticket 21](21-scan-time-budget.md) already warned — "cannot be
honestly substituted with a local run." No absolute local wall-clock number from this
session should be treated as ground truth.

**First decision (superseded within this same session):** split the scheduled scan into
two sequential jobs in `.github/workflows/alert.yml`. This was proposed to the user as a
mitigation for the measured 235s figure *before* that figure was shown to be sandbox noise
(see above) — the user was choosing a mitigation on evidence that later turned out to be
unreliable. Once that was disclosed, **the user chose to revert the workflow split and run
a single unsharded `scan` job, deliberately, to get one real GitHub Actions observation
before adding any workflow complexity.** `.github/workflows/alert.yml` is back to exactly
its pre-ticket form (verified `git diff` empty against `main`).

**What was kept:** `shard_sources()` and `job_alert.py scan --shard N --shard-count M`
remain in the codebase, tested, and dormant — nothing in the scheduled workflow calls them.
If a real Actions run shows the 195-source scan is actually approaching the 240s/300s
budget, re-enabling the split is a workflow-only change (add `scan-shard-1`, point each job
at `--shard {0,1} --shard-count 2`); the fetch-side logic doesn't need to be rebuilt.
`--shard-count` above 2 would additionally need the aggregator double-fetch question settled
(`simplify`/`ambicuity` currently run in every shard unconditionally) and a matching third
workflow job — flagging this now so a future session doesn't assume the flag alone is a
drop-in lever.

The duplicate-notification-on-failed-push exposure analyzed while the split was live
(bounded to a failed git push landing between two shards, and only actualized for a proven
Cross-post) is moot with a single scan job — noted here only so the analysis isn't lost if
the split is revisited.

## Acceptance

- [x] `sources.json` updated with the 21 verified slugs, no cross-platform duplicates
      (`growth_guardrail.duplicate_source_names` returns `{}`).
- [x] `job_alert.py` gains `shard_sources()` and `--shard`/`--shard-count`, tested and
      available but not wired into the scheduled workflow.
- [x] `.github/workflows/alert.yml` unchanged from its pre-ticket form — single `scan` job,
      full inventory, by explicit user decision.
- [x] `tests/test_source_inventory.py` updated for the new counts (100/5/82, 195 total
      fetches) and gained a shard-partition test (no overlap except the two aggregators,
      full coverage, balanced split) and a duplicate-slug regression test.
- [x] Full suite green: `.venv/bin/python -m unittest discover -s tests` — 142 tests, OK.
- [x] `growth_guardrail.py --baseline-ref <HEAD>` run locally: within limits (13.2 MB,
      ~0.25s medians, 16.1 MB packed Git) — Expansion Gate not remotely close to active.

**Explicitly NOT settled here, and inherited as open risk, same as ticket 21 left it:** an
observed end-to-end Actions wall-clock for the (now 195-source, unsharded) scan. **Watch the
first few scheduled runs after this merges.** If a run approaches or hits the 5-minute
timeout, the fix is re-enabling the shard split described above — not re-litigating which
companies belong in `sources.json`.

## Blocked by

_(nothing — frontier)_

## Related work

- [Assemble the UK sponsor-company list and verify board slugs](19-uk-sponsor-company-list.md)
  — same verification discipline (observed date, non-empty, correct company, net-new only).
- [Fit the expanded Source Inventory to the scan-time budget](21-scan-time-budget.md) —
  flagged the exact risk this ticket hit, and the local-measurement caveat this ticket
  confirms empirically.
- [Assemble the target company list and its board slugs](../../tickets/06-target-company-list.md)
  — prior art on the FAANG/proprietary-ATS exclusion this ticket reuses.
