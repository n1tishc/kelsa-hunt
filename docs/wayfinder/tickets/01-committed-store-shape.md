# Decide the committed store's shape

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

What artifact does the scan workflow commit on every run, and what is derived from it
rather than stored?

Today it commits one 6.5 MB `jobs.json` containing all ~13k Records, and rewrites
~21,300 lines of it per run because `last_seen` refreshes on nearly every record still
live in a feed. Seven bot commits produced 10.7 MiB of loose objects. The configured
`*/15` weekday cron wants ~40 runs/day, and source expansion multiplies both the record
count and the per-run churn.

Options to grill, not a menu to pick from blind:

- Keep one JSON blob but stop the churn (e.g. drop `last_seen` precision to a day, or
  keep volatile fields out of the committed file entirely)
- Split hot (open, recent) from cold (closed, aged) into separate files so most commits
  touch only the hot one
- Commit a SQLite file instead — smaller, but binary, so git can't delta it at all
- Commit nothing per-run; keep state in Actions cache / artifacts and treat the repo copy
  as a periodic snapshot
- Accept the growth and plan for periodic history rewrites

This blocks most of the map: the dashboard has to read whatever this produces, an Excel
export would be another copy of it, and "more sources" scales whatever cost it settles on.

**Resolve with a measurement, not a preference.** The numbers above are real; project
them forward for the source counts the expansion tickets are likely to land on.

## Blocked by

_(nothing — frontier)_

## Resolution

Resolved with the user on 2026-07-30.

`jobs.json` remains the single **Canonical Store**: the authoritative, permanent,
public ledger of every Record the system has seen. Dashboard data, exports, and
reports are **Derived Views**. They own no state, need not be committed beside the
store, and must be safe to delete and regenerate. Fetch timing and source-health
telemetry belong in operational workflow logs, not in every Record.

The Canonical Store persists meaningful Record state only:

- Keep `first_seen`, the source-provided `posted` value, `closed_at`, and
  `notified_at`.
- Remove per-scan `last_seen`; no operational behavior depends on it.
- Change store-level metadata only when Record state changes. A scan that observes no
  new Record or state transition must produce no store diff and therefore no commit.

Keep the store as one human-readable JSON file. Do not split it into hot/cold files,
replace it with SQLite, or move its authority into Actions cache:

- Hot/cold partitioning adds movement and reconciliation rules without reducing total
  checkout size.
- SQLite creates opaque binary Git diffs.
- Actions cache is evictable and cannot be the permanent ledger.

Measured basis: the current store contains 12,918 Records in 6.49 MB. The verified
source expansion is projected to produce roughly 31,765 Records and a 15.2 MB store
at the current Record shape. That is acceptable for Python loading and serialization;
dashboard delivery is not a constraint because the dashboard consumes a Derived View.
