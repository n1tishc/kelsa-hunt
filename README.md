# US/UK new-grad job alerter

Polls the Simplify and Ambicuity community new-grad feeds plus 173 configured
Greenhouse, Lever, Ashby, SmartRecruiters, Workable, and Recruitee boards, filters
to eligible US/UK entry-level SWE/MLE roles, and pushes new hits to Discord.

The Canonical Store is recall-first: every fetched Record is retained, including
roles that fail the current score, age, or location filters. Notifications are
precision-first and currently target Bay Area or explicit US-remote roles plus
major UK cities or explicit UK-remote roles. Location eligibility fails closed;
bare `Remote`, global, unknown, and foreign-only locations are never notified.

The active expansion branch is `docs/update-project-context`. It contains the
UK-aware classifier, region predicates, verified UK source inventory, and scan
budget instrumentation. The public Pages ledger remains the deployed US view
until the region-presentation work is merged and deployed from `main`.

## Setup

1. **Keep the repo public.** The best-effort schedule targets about 690 runs
   per month. Monitor actual usage against an operational ceiling of 1,000
   runner-minutes and keep normal p95 scans under 60 seconds; the five-minute
   job timeout is failure containment, not a per-run budget. Public Actions
   runners keep that capacity outside a private-repo minutes budget.
   Fetched Records are intentionally public; the Discord webhook stays in
   Secrets and personal application annotations stay gitignored.

2. **Create the Discord webhook.** In your server: Channel → Edit Channel →
   Integrations → Webhooks → New Webhook → Copy URL. No bot, no OAuth.

3. **Add it as a secret.** Repo → Settings → Secrets and variables → Actions →
   New repository secret, named `DISCORD_WEBHOOK`.

4. **Seed the state.** Run once with seeding on so you don't get 200 pings at
   once for roles that were already open:
   ```
   python job_alert.py scan --seed
   ```
   Or trigger the workflow manually with the `seed` input checked. Commit the
   resulting `jobs.json`.

5. Done. It runs itself from then on.

## Tuning

| Flag | Effect |
|---|---|
| `--min-score 3` | Include the "maybe" bucket (bare `Software Engineer` etc.) |
| `--min-score 10` | Only explicitly-labelled new-grad roles |
| `--no-remote` | Bay Area only, drop remote listings |
| `--dry-run` | Print matches, send nothing, don't touch state |

Scores: **10** = explicit new-grad wording, **5** = junior marker (`Engineer I`,
`Associate`, MTS), **3** = bachelors-eligible only. Embed colour tracks score.

Location filtering fails closed: US local roles need recognized US evidence and
US-remote roles must explicitly say US/USA/United States or name a US state or
territory. UK roles need explicit UK evidence; UK notifications are limited to
major cities such as London, Edinburgh, Manchester, Belfast, Leeds, Cambridge,
Bristol, Newcastle, Birmingham, Glasgow, or Cardiff, or explicit UK-remote.

Run `--dry-run --min-score 3` for a week and watch what lands in the maybe pile
before you tighten anything.

Discord delivery adapts to each scan's Notification Batch. Up to five Candidates
keep the rich per-Candidate embeds. Larger Batches use lossless digest pages of at
most ten rows, ordered by Score and freshness before stable presentation fields.
If a source omits its direct opening URL, the compact title links to a targeted
company-and-title search instead of becoming unactionable text.
Each accepted page is stamped and saved before the next page is attempted. If a
later page fails, the run fails while the accepted pages remain notified and the
undelivered Candidates remain pending for the next scan.

## Public job ledger

GitHub Pages publishes a read-only spreadsheet ledger after—and only after—a
meaningful `jobs.json` change. The workflow derives a compact strict-US data file,
copies the static ledger into one ephemeral Pages artifact, and never commits the
generated files. Open Records at Score 3+ are shown initially; search and status,
source, and Score controls expose the complete US history, including Score 0.

The deployed US ledger is <https://n1tishc.github.io/kelsa-hunt/>. Pages must use
**GitHub Actions** as its publishing source; the repository's custom `job-alert`
workflow already builds and deploys the artifact, so do not install GitHub's suggested
Jekyll or Static HTML starter workflow.

Enable Pages with **GitHub Actions** as its source in the repository settings. To
preview the exact artifact locally without touching the Canonical Store:

```sh
python3 scripts/build_dashboard.py jobs.json dashboard-dist
python3 -m http.server 8765 --directory dashboard-dist
```

Then open <http://127.0.0.1:8765>. `dashboard-dist/` is gitignored. The builder
reads raw `jobs.json` through an explicit public-field allowlist, so local
`applied_at` and `hidden` annotations cannot enter the artifact.

## Canonical Store growth guardrail

Every scan reports Record count, serialized bytes, Store load/save timing, and
end-to-end wall-clock duration. A scan-duration warning starts at 240 seconds,
leaving one minute inside the five-minute Actions timeout. The expanded inventory
is measured on GitHub Actions because runner/network behavior is the relevant risk.
The separate `growth-guardrail` workflow runs on every pull request, monthly from a
full-history packed checkout, and whenever `sources.json` changes on `main`. It warns at 20 MiB,
a 1.6-second five-round-trip median, or 200 MiB packed Git history. Further
source-count growth is blocked at 25 MiB, two consecutive 2-second medians, or
250 MiB packed history; existing scans, storage, notifications, and dashboard
deployments continue.

The check is named `check` in GitHub's rules UI. Do not make pull requests or status
checks globally mandatory on `main` while `job-alert` still commits `jobs.json` there
with the built-in Actions token: that would block Canonical Store persistence unless
the automation has a supported bypass. The check still reports on every pull request.
When the gate activates, the stated next response is deterministic 16-way UID sharding.
The check never migrates, prunes, or rewrites the Canonical Store or Git history
automatically.

The inventory guard also rejects a company slug configured on multiple ATS
platforms, because Opening Identity is platform-scoped and cannot safely deduplicate
such Records across platforms.

## Adding sources

`sources.json` takes Greenhouse, Lever, Ashby, SmartRecruiters, Workable, and
Recruitee board slugs.
The slug is the company segment in the board URL (`job-boards.greenhouse.io/SLUG`,
`jobs.lever.co/SLUG`, `jobs.ashbyhq.com/SLUG`, or
`jobs.smartrecruiters.com/SLUG`), or the hosted account segment in
`apply.workable.com/SLUG`, or the careers-site subdomain in
`SLUG.recruitee.com`. The Workable and Recruitee public endpoints return
complete published collections rather than paginated pages. Add companies as you
notice them missing. Some companies migrate between ATSs over time — if a
configured slug starts returning zero jobs, check whether the company moved
boards rather than assuming the role's just gone.

Ambicuity is enabled by the `ambicuity/New-Grad-Jobs` entry. Its Records remain
source-specific in the Canonical Store. A derived Cross-post Group forms only when
the direct employer URL exposes an Opening Identity recognized by the ATS registry;
similar company, title, or location text never triggers production deduplication.

## Applied tracking stays private

`jobs.json` is committed to the repo (it has to be — the scan workflow needs
it as persistent state, and the repo is public per above). But `applied_at`
and `hidden`, set via `python job_alert.py applied <needle>`, are personal —
they reveal which companies/roles you've actually applied to. Those two
fields live in `annotations.json` instead, which is gitignored and never
committed. Fetched job data (title, company, location, score, whether you've
been notified) stays in the public store; your application history doesn't.
