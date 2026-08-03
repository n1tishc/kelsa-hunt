# Handoff — 2026-08-01

Current operational and implementation state for the next session. Read
[map.md](map.md), `CONTEXT.md`, and
[`docs/adr/0001-repo-public-annotations-private.md`](../adr/0001-repo-public-annotations-private.md)
for the settled product and domain decisions.

## Current state

- The planned implementation sequence is complete through GitHub issue #11. The final
  guardrail correction was merged in [PR #12](https://github.com/n1tishc/kelsa-hunt/pull/12).
- The repository is public and `main` is the default branch.
- GitHub Pages is enabled with the custom Actions workflow. The public strict-US ledger
  is live at <https://n1tishc.github.io/kelsa-hunt/>. A verified 2026-08-01 manual run
  completed `scan`, `dashboard`, and `deploy` successfully.
- The Canonical Store currently contains 24,650 Records, serialized to 11,068,104 bytes,
  and was last updated at `2026-08-01T18:51:52+00:00`.
- The active Source Inventory is 110 feeds: 109 entries in `sources.json`, plus the
  built-in Simplify feed. It covers Greenhouse, Lever, Ashby, SmartRecruiters, Workable,
  Recruitee, Ambicuity, and Simplify.
- The most recent local growth check reported Store timing medians of roughly 0.21
  seconds and no active Store-size or timing gate. Packed Git size is authoritative only
  in the full-history monthly Actions run, not an unpacked local checkout.
- The complete test suite contains 90 tests and passed after issue #11 and its required
  check correction.

## Implemented behavior

- **Stable Canonical Store:** unchanged scans do not rewrite `jobs.json`; Records remain
  permanent, and source-scoped closure/reopening transitions remain reversible.
- **Strict-US boundary:** notifications, queries, exports, and dashboard data share the
  same fail-closed US policy. Bare remote, global, unknown, and foreign-only locations
  stay in history but do not enter user-visible Derived Views.
- **Proven Cross-post identity:** source Records stay separate. Only recognized,
  platform-scoped Opening Identities form Cross-post Groups; notification state covers
  every proven sibling.
- **Reliable scans:** eight workers fetch concurrently, with at most four requests per
  host, a ten-second request budget, isolated retries, and no closure evidence from a
  failed or suspiciously empty source.
- **Expanded coverage:** SmartRecruiters, Workable, Recruitee, and Ambicuity adapters are
  active alongside the original feeds and verified company inventory.
- **Lossless Discord delivery:** small Batches use rich embeds; larger Batches use ordered,
  paged digests. Each accepted page is checkpointed, and a rejected page fails visibly
  without stamping undelivered Candidates.
- **Public Job Ledger:** a meaningful Store change builds an ephemeral, allowlisted,
  strict-US Pages artifact. Generated dashboard data is never committed, and private
  `annotations.json` state cannot enter it.
- **Growth guardrail:** normal scans report Record count, serialized bytes, and load/save
  duration. The dedicated workflow runs on every pull request, on Source Inventory pushes,
  monthly from packed full history, and manually. Its next response is deterministic
  16-way UID sharding; it never auto-migrates, prunes, or rewrites history.

## Operations

- `job-alert` runs approximately every 30 minutes during weekday Bay Area working hours
  and every two hours outside that window and on weekends. GitHub cron is best effort.
- `job-alert` commits meaningful `jobs.json` changes directly to `main`; dashboard and
  Pages deployment follow only when that persistence step reports a change.
- A ruleset that globally requires pull requests or status checks on `main` can block
  those bot state commits. Do not enable such a rule without first giving the persistence
  identity an explicit supported bypass or moving Canonical Store persistence to a
  separate state branch. The `check` job still runs on every PR even when it is not a
  mandatory repository rule.
- Pages uses **GitHub Actions** as its publishing source. Do not install the suggested
  Jekyll or Static HTML starter workflows; `.github/workflows/alert.yml` already owns the
  build and deployment.
- The Discord webhook belongs only in the `DISCORD_WEBHOOK` Actions secret. Never place
  it in source, documentation, logs, or committed configuration.

## Active work

**Superseded as of 2026-08-01:** a new effort is live —
[Map: UK roles alongside US in kelsa-hunt](uk-expansion/map.md). It carries execution
(decisions *and* code) and has seven open tickets numbered 15–21. Its frontier is tickets
15, 17, 18, and 19; tickets 18 and 19 are research and were fired as subagents at charting.

That map reopens exactly one settled decision from [map.md](map.md): the **US eligibility
boundary** becomes a two-region **Eligible Region** concept covering US and UK. Everything
else in the "Implemented behavior" section above still holds.

Note item 3 below: "sponsorship filtering" has since been decided *against* as a runtime
filter — measured at 27 usable rows in 24,650 Records — and reinterpreted as
company-level source curation. See the new map's charting decisions.

## Remaining optional work

Beyond the active UK effort, these have no committed schedule and should begin only from an
observed need:

1. Move automated Canonical Store commits to a dedicated state branch or use a narrowly
   scoped automation identity so `main` can be strictly protected without breaking scans.
2. Decide whether private applied/hidden tracking needs a durable workflow beyond the
   local gitignored `annotations.json` file.
3. Add historical analytics or sponsorship filtering only if normal dashboard use shows
   a concrete need.
4. Regenerate the root `graphify-out/` knowledge graph before relying on its reported
   34-node/66-edge snapshot; it still describes the pre-implementation 2026-07-30 state.

## Documentation status

- `docs/wayfinder/`, the prototype, research, and graph outputs are committed.
- The Wayfinder tickets preserve the decision trail; `map.md` records the settled route.
- `README.md` is the operating guide, while this file is the time-stamped handoff.
