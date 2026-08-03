# Make classify() UK-title-aware

<!-- wayfinder:grilling -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

How does `classify()` score UK title conventions correctly without corrupting the Score
Bands or silently re-scoring US Records?

`classify()` was tuned entirely on US wording. Measured against UK titles from the live
Store, it fails in two distinct ways:

| Title | Score today | Cause |
| --- | --- | --- |
| `Software Engineer - New Grad` | 10 | US phrasing hits `STRONG_POS` |
| `Graduate Software Engineer` | **5** | `graduate` sits in `WEAK_POS`, not `STRONG_POS` |
| `Graduate Software Developer` | 5 | same |
| `Software Engineering Graduate Programme` | 5 | survives only via "Software" |
| `Graduate Programme - Engineering` | 5 | survives only via "Engineering" |
| `Technology Graduate Scheme` | **0** | `ROLE_MATCH` rejects: "not an eng/ML role" |
| `DXC Graduate Programme` | **0** | same |
| `Graduate Trainee Programme` | **0** | same |
| `Analyst Programmer` | **0** | same; UK-common title with no US analogue |
| `Technology Analyst` | **0** | same |

So the UK's canonical explicit-new-grad wording is under-scored by a full band, and
big-employer grad schemes are invisible. Of 1,405 confirmed-UK Records, **492** are
rejected as "not an eng/ML role" and **194** as "no entry-level signal". The UK band-10
tier holds only 25 Records, so "show me the best UK matches" is not a view you can ask for.

The charted decision: promote UK new-grad wording to Band 10 **and** widen `ROLE_MATCH`
with UK vocabulary, accepting new Band 5 noise from non-engineering grad schemes.

### Two traps this ticket must handle

1. **`graduate` must MOVE, not be duplicated.** It is already in `WEAK_POS`
   (`job_alert.py:319`). Adding it to `STRONG_POS` while leaving it in `WEAK_POS` yields
   10 + 5 = **band 15** — which already happens today for
   `Software Developer (Graduate, 2027 start)` → 15. `CONTEXT.md` documents exactly three
   Score Bands (10 / 5 / 3). Band 15 is undocumented and must not be multiplied; decide
   whether it is a bug to fix or a band to document, and say which.
2. **`classify()` is region-blind.** Its signature is
   `classify(title, degrees=None, category=None)` — no location, by design, and Score is
   computed at query time so every change is retroactive over all 24,650 Records. There is
   therefore no such thing as a UK-only classifier change. Widening `ROLE_MATCH` with
   analyst / programme / scheme / technologist vocabulary **will** re-score US Records.

### What must be settled

- Which tokens move into `STRONG_POS`, and whether `graduate` qualifies unconditionally or
  only adjacent to a role word (`Graduate Software Engineer` yes; `Graduate Analyst`
  arguably no).
- What `ROLE_MATCH` gains. Candidates from live UK data: `programme`, `scheme`,
  `analyst programmer`, `technologist`, `technology analyst`, `graduate developer`.
- Whether `HARD_NEG` and `MID_LEVEL` misfire on UK titles. `HARD_NEG` matches `\bII\b`,
  `l[4-9]`, `e[4-9]` case-insensitively, and `MID_LEVEL` rejects `engineer 2`. Confirm no
  UK convention trips these accidentally — `CONTEXT.md` records the L4+/E4+ hard reject as
  a deliberate permanent choice validated against the *US* company list only, so revalidate
  it against whatever UK companies
  [the sponsor-company list](19-uk-sponsor-company-list.md) proposes.
- Whether placement and internship titles stay at Band 3. `Industrial Placement - Software`
  and `Placement Student - Software Engineering` currently score 3 via bachelors-eligible.
  That is arguably correct for a new-grad search — decide rather than inherit.

### Acceptance

- Score Bands remain exactly as `CONTEXT.md` documents them, or `CONTEXT.md` is updated to
  match reality. No accidental band 15.
- The delta is measured **on both regions** before committing. Use two different
  instruments, because one tool cannot see both — see the warning below.
- Report how many US Records change band and spot-check the newly-admitted ones. **A US
  regression is the real risk of this ticket, not a UK one.**
- Report the UK band-10 count before and after (25 today).
- Full test suite green, with new cases for each UK title form in the table above.

### Do not measure with `query` alone — it cannot see UK Records

`CONTEXT.md` and the archived map both say a classifier change "can be tested against all
~24.6k historical Records for free via `query --all --max-age 0 --min-score N`". **That claim
is wrong, and verified wrong on 2026-08-01.** `cmd_query` calls `Store.candidates()`, which
applies `strict_us_record()` (`job_alert.py:515`) *and* `is_bay_area()` (line 527) *and*
`dedup()` before returning. Observed: `query --all --max-age 0 --min-score 3` returns
**229** matches, not 24,650.

(`--max-age 0` is fine — line 534 reads `if max_age_days and ref and ref < cutoff`, so 0
disables the age gate as intended. The reach is lost to the location gates, not the age one.)

So while [the Eligible Region boundary](15-eligible-region-boundary.md) is open, `query`
returns **zero** UK Records, and a resolving session that measures the UK delta with it will
see "no change" and wrongly conclude the UK fix did nothing.

Use both of these:

- **US delta (the regression risk):** `query --all --max-age 0 --min-score N`, understanding
  it reports the Bay-Area-plus-US-remote deduped view — 229 rows at min-score 3 today — not
  all history.
- **UK delta, and any all-history sweep:** call `classify()` directly over `jobs.json`,
  bypassing the Store's Derived Views entirely. The charting measurements in
  [the map](../map.md) were taken this way — load `job_alert.py` via `importlib`, iterate
  `json.load(open('jobs.json'))['jobs']`, and call
  `classify(title, degrees, category)`, which returns `(keep, score, reason)`.

If this ticket resolves after ticket 15, re-check whether `query` has become region-aware and
prefer it — but verify rather than assume.

## Blocked by

_(nothing — frontier)_

Independent of the region work: `classify()` never reads location, so it can be tuned
before the Eligible Region predicate lands. Note both touch `job_alert.py`, though in
separate regions of the file (classifier at 306–380, location policy at 83–305).

## Related work

- [Re-tune the notification threshold and age gate](../../tickets/04-threshold-and-age-gate.md)
  — the settled Score 5+ threshold, MTS +5, and L4+/E4+ hard reject.
- [Assemble the UK sponsor-company list and verify board slugs](19-uk-sponsor-company-list.md)
  — supplies the UK companies whose leveling conventions need revalidating.
