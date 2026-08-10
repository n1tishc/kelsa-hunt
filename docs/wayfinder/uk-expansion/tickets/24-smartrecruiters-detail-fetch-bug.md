# Fix the SmartRecruiters detail-fetch bug that was the real scan-timing bottleneck

<!-- wayfinder:task -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

Requested directly: after seeing the first real sharded-scan observation (`scan`=30.52s,
`scan-shard-1`=197.65s — see
[ticket 23](23-second-source-batch-and-real-timing.md)), the user asked why one shard was
so much faster and whether that headroom meant more sources could safely be added. That
question demanded finding out *why* one shard was slow, not assuming it was safe to add
more load to the fast one.

## What was found: one source, not host congestion, not board count

Per-source fetch durations are already logged (`{name}: {count} listings ({status},
{duration:.2f}s)`). Pulling them from `scan-shard-1`'s actual log
(run `31431742922`, 2026-08-10) instead of guessing:

```
smartrecruiters/Wise: 406 listings (ok, 188.94s)
greenhouse/monzo: 77 listings (ok, 11.07s)
greenhouse/workato: 155 listings (ok, 10.58s)
... (everything else under 12s)
```

**`smartrecruiters/Wise` alone accounted for 188.94 of `scan-shard-1`'s 197.65 total
seconds** — 95.6% of that shard's wall-clock, from a single source. This is not a
host-congestion or shard-balance problem; it is one misbehaving source.

## Root cause

`fetch_smartrecruiters()` (`job_alert.py`) issues one paginated list request per 100
postings, then for each individual posting decides whether it needs an extra detail GET:

```python
needs_detail = not (
    posting.get("name")
    and isinstance(posting.get("company"), dict)
    and posting["company"].get("name")
    and isinstance(posting.get("location"), dict)
    and posting.get("postingUrl")   # <- the bug
)
```

**Observed 2026-08-10, live**, paginating all 406 Wise postings and all 2 Visa postings:
`name`, `company.name`, and `location` are always present on the list endpoint.
**`postingUrl` is never present on the list endpoint, for either tenant** — confirmed
across every one of Wise's 406 postings. Requiring it therefore made `needs_detail` true
for **every single posting on every SmartRecruiters board**, forcing one additional
sequential `GET` per posting (`get_json(ref)`, not parallelized — `fetch_smartrecruiters`
runs its own pagination/detail loop inside a single `ThreadPoolExecutor` worker, so all
406 detail requests happened one after another). For a 2-posting board like Visa this is
noise; for Wise's 406 it is nearly 3 minutes, every scan, forever, silently — nothing
about `growth_guardrail.py`'s aggregate `wall_seconds` metric pointed at *which* source
was responsible until the per-source log lines were actually read.

**Verified the detail endpoint's only real contribution was cosmetic.** The detail
response supplies a nicely slugified `postingUrl`
(`.../744000142727488-fincime-operations-senior-analyst-rfi`), but the bare
`https://jobs.smartrecruiters.com/{slug}/{id}` form — constructible from data already on
the list response — **returns `200` and resolves to the same posting** (Observed
2026-08-10, direct `curl`). The detail fetch was buying a prettier URL at a 60x latency
cost.

## Fix

Dropped `postingUrl` from the `needs_detail` check (it will never be satisfied from the
list response, so it was equivalent to "always fetch detail"). Added a constructed-URL
fallback so postings still get a working link without needing the detail call:

```python
"url": (
    normalized.get("postingUrl")
    or normalized.get("applyUrl")
    or f"https://jobs.smartrecruiters.com/{slug}/{posting['id']}"
),
```

`needs_detail` now stays true only when a posting is genuinely missing `name`, `company`,
or `location` from the list response — the case
`test_detail_resource_fills_fields_omitted_from_the_list` already covered and still
covers.

**Verified against live data (Observed 2026-08-10, post-fix):**

```
ok: True | count: 406 | elapsed: 3.15s
sample url: https://jobs.smartrecruiters.com/Wise/744000142727488
```

**189s → 3.15s. A ~60x reduction, for this source alone.** Applied against
`scan-shard-1`'s observed 197.65s, this predicts a corrected wall-clock of roughly
197.65 − 188.94 + 3.15 ≈ **11.9s** — comparable to `scan`'s own 30.52s, not the near-limit
number ticket 23 recorded. This is a prediction pending the next real scheduled run, not
yet a second observation.

**One-time side effect to expect:** every currently-stored `smartrecruiters:Wise:*` and
`smartrecruiters:Visa:*` Record's `url` field will change from the old slugified form to
the bare-ID form on the next scan that touches them, since the code path that produced
the slugified URL (the detail fetch) no longer runs. This is expected, not a regression —
both URL forms resolve to the same posting.

## Why this matters for the "just add more sources" question that prompted it

This reframes ticket 23's whole timing investigation. The 205–242s pre-sharding numbers,
the shard split, and the "is there headroom" question were all being reasoned about as if
wall-clock scaled with board *count*. It didn't — one board's detail-fetch bug was
responsible for the overwhelming majority of it. **The honest amount of real headroom in
the system was never really about sharding or board count; it was hidden behind this
bug.** Now that it's fixed, the sharding split may turn out to be unnecessary for the
current inventory size — that should be decided from the next real observation, not
assumed from this fix alone.

## Acceptance

- [x] `job_alert.py`: `needs_detail` no longer requires `postingUrl`; `url` falls back to
      a constructed `jobs.smartrecruiters.com/{slug}/{id}` link.
- [x] `tests/test_smartrecruiters.py`: updated `test_fetches_all_pages_and_normalizes_records`
      for the new URL form; added
      `test_never_fetches_detail_when_list_already_has_required_fields` as an explicit
      regression guard (asserts zero `/postings/{id}` detail calls when the list already
      has complete data).
- [x] Full suite green: `.venv/bin/python -m unittest discover -s tests` — 143 tests, OK.
- [x] Verified against live Wise data: 406 postings, 3.15s, correct company/title/location,
      working URL.
- [ ] **Not yet observed:** a real scheduled Actions run against this fix, to confirm the
      predicted ~12s `scan-shard-1` wall-clock and settle whether sharding is still
      warranted at the current 225-source inventory size.

## Blocked by

_(nothing — frontier)_

## Related work

- [Second source batch, and the real Actions timing that resolves ticket 22's open risk](23-second-source-batch-and-real-timing.md)
  — the observation (`scan-shard-1`'s per-source log) that led here.
- [Fit the expanded Source Inventory to the scan-time budget](21-scan-time-budget.md) —
  originally asked for real Actions timing; this ticket is the answer to *why* that
  timing looked the way it did.
