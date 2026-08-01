# Public repo, private application history

**Context:** At decision time, the workflow was configured for about 1,230 runs/month (15-minute working-hours cron, two-hour otherwise), and its 40–90 second runtime was estimated rather than measured. That put the projected private-repo usage near or above the included minutes budget. The workflow also commits `jobs.json`, and that public ledger was on track to carry `applied_at`/`hidden` annotations—which companies and roles the owner had applied to—into permanent, forkable Git history.

**Decision:** Keep the repo public for the Actions minutes. Split `applied_at` and `hidden` out of the tracked, public `jobs.json` into a separate, gitignored local file. The fetched job records themselves (title, company, location, score) and `notified_at` stay in the public, committed store — none of that is sensitive. Only the owner's personal application activity is kept out of git history entirely.

**Consequence:** Anything in the private annotations file doesn't survive a fresh clone or a different machine without being copied over manually — this is a deliberate trade for keeping application history off public record, not an oversight.

## Runtime update — 2026-07-31

The original cadence and cost projection are superseded. The workflow now targets about
690 best-effort runs/month (30-minute weekday working hours, two-hour otherwise), uses
bounded concurrent Source Fetches, and monitors actual usage against an operational
ceiling of 1,000 runner-minutes with normal p95 scans targeted below 60 seconds. The
five-minute workflow timeout contains failures; it is not the budget for every run.
The public-repo decision therefore no longer rests on the old claim that the private
minutes allowance would necessarily be exceeded. It remains the chosen operating model:
fetched Records are intentionally public, while the annotation split above remains the
privacy boundary.
