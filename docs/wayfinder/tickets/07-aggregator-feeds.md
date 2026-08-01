# Find aggregator feeds worth adding beyond Simplify

<!-- wayfinder:research -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

What other community-maintained or public new-grad job feeds exist that can be fetched as
structured data, and how much do they actually add over Simplify?

Simplify's `listings.json` supplies 10,215 of ~13k stored records — the tool leans on it
almost entirely, which is a single point of failure and a single point of view.

For each candidate feed establish:

- A machine-readable URL (raw JSON/CSV in a repo, or an API) — **not** a README table that
  would need HTML parsing, unless the value is exceptional
- Update cadence and whether it's actively maintained
- Field coverage, especially location and posted date
- **Estimated overlap with Simplify** — this is the deciding number. A feed that's 90%
  duplicate adds dedup load and near-zero signal.

Known starting points: the SimplifyJobs New-Grad-Positions repo already in use, the
related Summer/Off-season internship lists, and the various `*-new-grad-jobs` GitHub lists
that fork or mirror each other — mirrors are the main trap here, since they look like
independent sources and aren't.

Deliver: candidate feeds ranked by *unique* records contributed, with the overlap estimate
shown. Explicitly recommend against any feed that's mostly a mirror.

## Blocked by

_(nothing — frontier)_

## Resolution

Research completed 2026-07-30:
[Alternative New-Grad Job Feed Research](../research/07-aggregator-feeds.md).

The measured recommendation is to add `ambicuity/New-Grad-Jobs` after ticket 09
settles Cross-post identity. Its current `docs/jobs.json` contributed about 1,376
apparently distinct rows beyond active Simplify records in the snapshot. ApplyGuy and
ForgeApply are deferred; the Surya internship tracker and README-only lists are
rejected.
