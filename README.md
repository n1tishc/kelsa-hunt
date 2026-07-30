# Bay Area new-grad job alerter

Polls the Simplify community new-grad feed plus any Greenhouse/Lever boards
you list, filters to Bay Area entry-level SWE/MLE roles, and pushes new hits
to Discord.

## Setup

1. **Make the repo public.** GitHub Actions minutes are unlimited on public
   repos. On a private repo a 15-minute cron burns ~2,880 min/month, which
   blows past the 2,000-minute free tier. Nothing here is sensitive — the
   webhook lives in Secrets, not in the code.

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

Run `--dry-run --min-score 3` for a week and watch what lands in the maybe pile
before you tighten anything.

## Adding sources

`sources.json` takes Greenhouse, Lever, and Ashby board slugs — the slug is
the path segment in the board URL (`job-boards.greenhouse.io/SLUG`,
`jobs.lever.co/SLUG`, `jobs.ashbyhq.com/SLUG`). Add companies as you notice
them missing. Some companies migrate between ATSs over time — if a
configured slug starts returning zero jobs, check whether the company moved
boards rather than assuming the role's just gone.

## Applied tracking stays private

`jobs.json` is committed to the repo (it has to be — the scan workflow needs
it as persistent state, and the repo is public per above). But `applied_at`
and `hidden`, set via `python job_alert.py applied <needle>`, are personal —
they reveal which companies/roles you've actually applied to. Those two
fields live in `annotations.json` instead, which is gitignored and never
committed. Fetched job data (title, company, location, score, whether you've
been notified) stays in the public store; your application history doesn't.