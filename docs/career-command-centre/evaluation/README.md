# Bounded Application Studio evaluation

**Ticket:** [#30](https://github.com/n1tishc/kelsa-hunt/issues/30)
**Status:** technical spike ready; Vertex execution is blocked until Ticket #27's
owner-verified Free Trial credit/expiry and reminder dates are recorded.

This is a small, human-labelled, **de-identified** corpus for deciding whether a
direct no-tools Gemini workflow is useful enough to pursue. It compares two
advisory-only paths over the same frozen input:

1. deterministic title/metadata baseline;
2. one direct Vertex Gemini Flash structured-output call.

Every corpus example declares a small, human-reviewed catalogue of stable evidence
IDs. Gemini can select only those IDs; local code checks that each selected ID is both
declared and human-approved for that example before counting it. This avoids treating
word-for-word reproduction of a human-written claim as a quality requirement. The
model's summary is always an owner-review suggestion, never a verified fact.

Any malformed response, safety block, exception, invalid evidence selection, or
missing final output is an abstention/no proposal. The evaluator cannot enter
Candidate, Eligible Region, Score, source, or Discord paths, and it has no external
write/action tool.

## Run

Use a disposable virtual environment outside the repository and authenticate with the
dedicated trial project's existing ADC/WIF identity. Never place a service-account key
or project ID in this repository. After Ticket #27 is complete, create an untracked
local JSON file containing factual `trial_credit_usd`, `trial_expiry`,
`day_75_scheduled_at`, and `day_80_scheduled_at` values plus
`"reminders_retimed": true`. This is an execution admission control, not a replacement
for the owner's Cloud Billing review.

```bash
python3 -m pip install -r docs/career-command-centre/evaluation/requirements.txt
python3 scripts/evaluate_application_studio.py \
  --project "YOUR_DEDICATED_TRIAL_PROJECT" \
  --trial-facts /private/tmp/kelsa-trial-admission.json \
  --admit-vertex \
  --output /private/tmp/kelsa-application-studio-evaluation.json
```

The optional output is aggregate-only: corpus inputs, prompts, raw model responses,
and private identifiers are never emitted. It reports selected-evidence
support/correctness, verdict alignment/usefulness against the human label,
rejected-proposal/safe-abstain and safe-failure rates, median latency, and Vertex response token
totals. Cloud Billing—not this script—is the cost source of truth.

If an execution environment has a short command lifetime, use `--offset` and
`--limit` to run a small deterministic slice (for example, `--offset 0 --limit 2`).
Each batch is independently aggregate-only; do not mix results from different corpus,
prompt, schema, or model versions.

## Human decision rule

Compare the two aggregate rows. The direct path earns a follow-up only when it has
strong human-aligned verdicts and evidence selection without an unacceptable abstention,
safe-failure, latency, or token signal. A model result is never a policy decision; a
human must review the aggregate and underlying de-identified evaluation record before
any private product work begins.
