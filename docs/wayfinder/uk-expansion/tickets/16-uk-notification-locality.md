# Set the UK notification locality tier

<!-- wayfinder:grilling -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

What is the UK peer of `BAY_TERMS`, and does `is_bay_area()` generalize into one
region-keyed notification-locality predicate?

The charted decision is that UK mirrors the US two-tier shape: the whole UK is *visible*,
while major UK cities plus UK-remote is what *notifies*. That mirrors today's asymmetry
exactly — `strict_us_record()` gates visibility across all of the US, while
`is_bay_area(locations, allow_remote=True)` narrows *notification* so
`Store.candidates()` reads Score ≥5 **and** (Bay Area **or** explicit US-remote).

So this ticket is the notification tier only. Visibility is
[the Eligible Region boundary](15-eligible-region-boundary.md)'s job.

### What must be settled

- **The design question, not the list.** Does `is_bay_area()` become
  `is_notify_locality(record)` dispatching on the Record's region, or does a separate
  `is_uk_major_city()` sit beside it? `CONTEXT.md` states that additions to `BAY_TERMS` are
  *data changes, not design decisions* — the UK tier should inherit that property, so
  adding Sheffield later is a one-line data edit.
- **The city list itself.** Live UK Records cluster as: London (879 across four string
  forms), Edinburgh 37, Manchester 29, Belfast 23, Leeds 19, Cambridge 17, Bristol 17,
  Newcastle upon Tyne 15, Birmingham 13, Glasgow 12, Cardiff 9. Reading, Oxford,
  Sheffield, Nottingham, Liverpool, Brighton were in the charting sweep but are thin or
  collision-prone. Decide the starting set and note explicitly which were considered and
  left out, so "for now" has a recorded boundary.
- **Metro grouping.** `BAY_TERMS` is one metro spanning many municipalities (SF plus
  peninsula, south bay, east bay). Is the UK tier a flat list of cities, or does London
  similarly absorb surrounding commuter locations (Croydon, Reading, Slough, Watford)?
  This is a genuinely different structure from the US case, not a translation of it.
- **UK-remote.** `allow_remote=True` currently pairs Bay-Area matching with explicit
  US-remote. The UK equivalent must pair with explicit UK-remote — the 78 live
  `Remote - UK` / `Remote in UK` / `Remote - United Kingdom` / `Remote, United Kingdom`
  Records — and must not admit bare `Remote`.
- **Collision safety.** Cambridge, Birmingham, Brighton, and Newcastle all appear in the
  live Store with US state codes attached. The notification tier must not re-open a
  collision that ticket 15 closed; it should consume ticket 15's region decision rather
  than re-testing city strings itself.
- **`CONTEXT.md`.** The *Bay Area* entry is scoped as "notification-locality scope". Add
  the UK peer as a sibling entry with the same framing.

### The coupling to break — verified 2026-08-01

`is_bay_area()` (`job_alert.py:277`) **hard-codes the US filter inside itself**: its first line is
`for loc in us_locations(locations)`, and its remote branch calls `us_locations([part])` again.
So the locality tier is not merely US-*shaped* — it is US-*bound* at the implementation level. A
generalized `is_notify_locality(record)` cannot call `us_locations()`; it has to filter by the
record's own region.

Two related observations, so the resolving session does not chase either one:

- `Store.candidates()` looks asymmetric — line 515 computes `rec = strict_us_record(source_rec)`
  but line 527 passes the **unfiltered** `source_rec.get("locations")` to `is_bay_area()`.
  Verified: this is **cosmetic, not a bug**, because `is_bay_area()` re-filters internally and
  `us_locations()` is idempotent. Don't "fix" it in isolation — but note the region generalization
  must not turn it into a real asymmetry.
- `BAY_TERMS` already handles collisions by **state-qualifying** ambiguous names: `newark, ca`,
  `dublin, ca`, `concord, ca` (guarding Newark NJ, Dublin Ireland, Concord NH). Adopt the same
  discipline for any ambiguous UK city rather than inventing a new mechanism.

### Acceptance

- One notification-locality concept covering both regions; adding a city stays a data edit.
- `Store.candidates()` applies the region-appropriate locality tier without a second copy
  of the Bay Area logic.
- Tests cover each starting UK city, UK-remote in all four live string forms, bare
  `Remote` still failing closed, and the collision cities resolving to the correct region.
- The US Candidate set is unchanged by this ticket.

## Blocked by

- [Define the Eligible Region boundary](15-eligible-region-boundary.md) — the locality tier
  narrows within a region, so region resolution and its collision rules must settle first.

## Related work

- [Re-tune the notification threshold and age gate](../../tickets/04-threshold-and-age-gate.md)
  — Score 5+ and the 21-day gate stay as settled; only locality changes here.
- [Set notification UX at expanded source volume](../../tickets/13-notification-ux-at-expanded-volume.md)
  — 26 UK Records notify on first open, which its paged digest already handles losslessly.
