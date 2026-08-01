# Source inventory validation — 2026-08-01

Ticket #5 activated the target-company research inventory: 73 Greenhouse boards,
one Lever board, and 31 Ashby boards. Together with Simplify and the separately
configured Visa SmartRecruiters board, a normal scan schedules 107 Source Fetches.

## Read-only validation

The configured adapters were fetched through `fetch_sources()` and their successful
responses were normalized into a `Store` created in a temporary directory. The run did
not invoke `cmd_scan()`, Discord, `Store.save()`, or the production `jobs.json`.

| Measurement | Result |
|---|---:|
| Elapsed fetch time | 4.17 seconds |
| Configured Source Fetches | 107 |
| Healthy | 106 |
| Failed | 1 |
| Manual verification required | 0 |
| Normalized Records | 22,932 |
| Unique source UIDs | 22,932 |
| Records missing canonical keys | 0 |
| Strict-US Records | 16,120 |
| Score 5+, at most 21 days old | 67 |

`greenhouse/coursera` returned HTTP 404. Its failure was isolated: the other 106
sources completed and its result supplied no closure evidence. Coursera remains in
the configured inventory because it is part of the research-approved 73-board set;
the failed endpoint should be re-verified before that research inventory is revised.

The 4.17-second fetch stage is inside the agreed normal p95 target of 60 seconds and
the five-minute workflow failure-containment limit.
