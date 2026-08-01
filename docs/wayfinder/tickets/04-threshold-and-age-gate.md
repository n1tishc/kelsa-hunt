# Re-tune the notification threshold and age gate against full history

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

Are `--min-score 5` and `MAX_AGE_DAYS = 21` the right gates, given what the full store
actually contains?

Measured 2026-07-30 against ~13k records: **91** open Bay Area Records score ≥5 all-time,
but **65 of them are older than 21 days**, so the age gate excludes the large majority of
qualifying roles. In 7 runs after seeding, 37 new records arrived and **zero** cleared
all three gates together. That may be correct precision — or the gates may be tuned so
tight the tool has nothing to say.

Things to pull apart:

- Does the age gate belong at 21 days, and should it use `posted` at all? For Greenhouse
  the `posted` value is `updated_at`, which refreshes on any edit — so "age" already
  means different things per source.
- Is Score Band 3 genuinely a manual-sweep tier, or is it the tier that would have
  surfaced most of the 65?
- The MTS +5 and L4+ hard-reject rules are marked permanent in `CONTEXT.md`. Confirm they
  still hold against the full store rather than assuming.

**This is cheap to answer.** `classify()` runs at query time and is never persisted, so
every variant can be evaluated retroactively over complete history:
`python job_alert.py query --all --max-age 0 --min-score N`. Bring numbers, not opinions.

Note this ticket sets thresholds for *today's* source coverage. The expansion tickets will
change the volume underneath it; the fog entry "Notification UX at higher volume" is where
that gets revisited.

## Resolution

Resolved with the user on 2026-07-31. Keep the current notification policy:

- The Notification Threshold remains Score `5`. Score Band 3 remains available through
  the dashboard and manual queries, but does not notify automatically. At the 21-day
  gate, lowering the threshold from 5 to 3 would increase the current set from 34 to 61
  open Records, mostly through generic bachelors-eligible titles rather than explicit
  junior signals.
- The age gate remains 21 days. The current store has 34 open Score 5+ Records inside
  21 days, 51 inside 30 days, and 120 without an age limit. Every one of those Records
  was first seen during the initial import, so the pre-fix silence provides no reliable
  evidence that 21 days is too strict; older Records remain browsable without generating
  backfill notifications.
- Measure age from the Freshness Timestamp: the best source-provided activity time,
  falling back to `first_seen` only when none exists. This avoids treating an entire
  newly added source catalogue as freshly posted. Greenhouse `updated_at` is accepted as
  recent source activity rather than misrepresented as a uniform creation date.
- Keep MTS at +5. Only three open, US-eligible MTS Candidates remain in the current
  snapshot, and explicit senior markers still reject senior MTS titles.
- Keep L4+/E4+ as a hard reject. The full store provides no counterexample in which a
  current source uses those levels for a new-grad role, while senior/numeric-level rules
  exclude 2,436 Records of obvious noise.

These gates should be reconsidered after source expansion produces reliable post-fix
arrival data. Delivery behavior at that volume remains owned by
[Set notification UX at expanded source volume](13-notification-ux-at-expanded-volume.md).

## Blocked by

- [Fix the two ways notifications get lost silently](03-fix-notification-loss.md) — until
  losses are fixed, low observed alert counts can't be attributed to threshold choice.
