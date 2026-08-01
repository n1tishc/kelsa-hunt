# Ambicuity overlap validation — 2026-08-01

This read-only measurement was completed before Ambicuity was added to normal scan
configuration. Both moving branch artifacts were downloaded to temporary files; no
Canonical Store or notification state was loaded or changed.

## Pinned inputs

| Feed | Commit | SHA-256 | Population |
|---|---|---|---:|
| `ambicuity/New-Grad-Jobs` `docs/jobs.json` | `d05beb1d4826ee88d7d977d55823fbce1fa3fa17` | `2d0592bf6c9e3b297fe77f3464a57a7184e704df83948b3bf019791233f520f5` | 1,485 |
| `SimplifyJobs/New-Grad-Positions` `listings.json` | `52f35cf15c7e4f5e42b66037cfe721b72757c680` | `b951f6a00d7b33a2a52247acae3c6b13fc07e41294759c3419b587ff5e240871` | 2,672 active and visible |

Ambicuity reported `meta.generated_at` as
`2026-08-01T09:26:31.575971+00:00`.

## Result

| Measurement | Rows |
|---|---:|
| Proven Opening Identity matches | 58 |
| Measurement-only exact company/title plus compatible-location matches | 2 |
| Total measured overlap | 60 (4.0%) |
| Apparently unique Ambicuity rows | 1,425 |

Only the 58 proven Opening Identity matches are eligible for production Cross-post
grouping. The two description/location matches are measurement evidence only; they do
not authorize fuzzy production deduplication. “Apparently unique” means unmatched by
this conservative comparison, not proof that every row is a distinct requisition.

## Reproduction

After downloading the two files at the commits above:

```sh
python3 -m scripts.measure_ambicuity_overlap \
  /path/to/ambicuity-jobs.json /path/to/simplify-listings.json \
  --ambicuity-commit d05beb1d4826ee88d7d977d55823fbce1fa3fa17 \
  --simplify-commit 52f35cf15c7e4f5e42b66037cfe721b72757c680
```

The comparison code is [the overlap measurement module](../../scripts/measure_ambicuity_overlap.py).

## Activation validation

The completed adapter was then run read-only against the same pinned feed. It
normalized all 1,485 rows into 1,485 unique source UIDs: 1,476 live Records and nine
source-closed Records. Five rows with a nullable company name were retained with an
empty presentation value. The direct URLs yielded 1,156 identities recognized by the
production Opening Identity registry. No Store was loaded or saved during this check.
