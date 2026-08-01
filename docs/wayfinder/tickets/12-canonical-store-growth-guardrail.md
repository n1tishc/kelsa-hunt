# Set the Canonical Store growth guardrail

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

At what measured threshold does the single-file Canonical Store stop being acceptable,
and what is the first response when it crosses that threshold?

[Decide the committed store's shape](01-committed-store-shape.md) chose one stable
`jobs.json`, projected at roughly 15.2 MB after the currently proposed source
expansion. Records remain permanent, so the file will continue growing even after
per-scan heartbeat churn is removed.

Set objective guardrails rather than waiting for a vague sense that the store is
“large”: serialized file size, Python load/save time, checkout time, Git repository
growth, or a combination. Then choose the first escalation path—shard the Canonical
Store without pruning Records, archive immutable cohorts, or another reversible
structure. Any policy that deletes Records conflicts with the established permanent
ledger and requires an explicit domain decision.

## Resolution

Resolved with the user on 2026-07-31 using the user's approved recommended defaults.
Keep the single-file Canonical Store through the planned expansion, but declare it over
the guardrail when any one of these hard limits is reached:

- serialized `jobs.json` size: **25 MiB**;
- median Python load plus save time: **2 seconds** on the supported Actions runner,
  measured over five round trips; or
- packed full-history `.git` size: **250 MiB**.

Warn at 80% of any limit: 20 MiB, 1.6 seconds, or 200 MiB. File and packed-history
sizes are deterministic and trigger immediately. A timing breach must repeat in two
consecutive checks to avoid reacting to runner noise.

Measured 2026-07-31:

- the current 12,918-Record store is 6.49 MB (6.19 MiB), with median 29 ms load and
  104 ms save;
- a temporary 31,765-Record projection is 15.89 MiB, with 69 ms load and 276 ms save;
- 50,000 current-shape Records produce 25.25 MiB, with 119 ms load and 503 ms save;
- 100,000 produce 50.51 MiB, with 253 ms load and 983 ms save; and
- the current repository is 24.34 MiB as loose objects, while a temporary packed clone
  is 6.8 MiB and cloned locally in 0.16 seconds.

The planned 31,765-Record expansion therefore fits below every hard limit with useful
headroom. Report Record count, serialized bytes, and load/save duration in normal scan
logs. Run the packed-history measurement monthly from a full-history checkout; shallow
scheduled scans cannot measure it honestly.

Crossing a hard limit pauses **further source expansion**, not existing scans, storage,
dashboard builds, or notifications. The first response is a reversible deterministic
16-way shard of the Canonical Store by stable hash of `uid`, plus a small manifest. This
keeps every Record, prevents source-size skew, avoids moving Records between hot and cold
files, and lets meaningful changes rewrite only affected shards after heartbeat churn is
removed.

The migration must verify identical Record count and content before switching readers,
retain legacy single-file read support during the transition, and preserve the Store API
for Candidates and Derived Views. Do not prune Records, archive Closed Records as the
first response, make SQLite authoritative, or rewrite Git history. Re-evaluate the same
limits after sharding rather than treating sharding as unlimited capacity.

## Blocked by

- [Decide the committed store's shape](01-committed-store-shape.md) — resolved
  2026-07-30; its single-file decision makes this threshold question concrete.
