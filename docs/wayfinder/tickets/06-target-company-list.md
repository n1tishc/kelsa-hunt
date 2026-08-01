# Assemble the target company list and its board slugs

<!-- wayfinder:research -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

Which Bay Area companies should `sources.json` cover, and what is each one's board slug on
its current ATS?

`sources.json` today lists 12 slugs: 8 Greenhouse (anthropic, databricks, stripe, figma,
scaleai, airtable, vercel, attentive), 4 Ashby (notion, benchling, ramp, plaid), 0 Lever.
That's a hand-written starter list, and it's the reason coverage feels thin.

Produce a candidate list — target 100+ companies — covering Bay Area employers that
actually hire new-grad SWE/MLE: big tech, AI labs, established startups, fintech,
infrastructure. For each: company name, ATS platform, board slug, and **verification that
the slug currently returns jobs**, since the slug is the failure-prone part.

Two things to get right:

- **Verify, don't guess.** An unverified slug is worse than a missing one — it fails
  silently and looks like the company just isn't hiring.
- **Note which are direct-board-only.** Companies already well covered by the Simplify
  feed add less than companies Simplify misses; the marginal gain is what matters.

Deliver a proposed `sources.json` plus a short note on which additions are high-value vs.
redundant with Simplify.

## Blocked by

_(nothing — frontier)_

## Resolution

Research completed 2026-07-30:
[Target company list and verified board identifiers](../research/06-target-company-list.md).

The corrected result contains 107 verified employers: 105 non-empty boards supported
by the current fetchers and two verified direct boards. Its proposed `sources.json`
payload adds 93 boards. LendingClub was removed after its initially verified
Greenhouse endpoint returned 404 in the same-day runtime benchmark.
