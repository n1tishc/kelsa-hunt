# Bounded Application Studio evaluation

**Ticket:** [#30](https://github.com/n1tishc/kelsa-hunt/issues/30)
**Status:** technical spike ready; Vertex execution is blocked until Ticket #27's
owner-verified Free Trial credit/expiry and reminder dates are recorded.

This is a small, human-labelled, **de-identified** corpus for deciding whether the
fixed no-tools ADK workflow earns its complexity. It compares three advisory-only
paths over the same frozen input:

1. deterministic title/metadata baseline;
2. one direct Vertex Gemini Flash structured-output call;
3. Role Analyst → Career Strategist → Application Writer → Evidence Critic as four
   fixed ADK `LlmAgent`s using an in-memory session and **no tools**.

The script validates every returned Evidence Card locally: the card's source ID must
be declared by the corpus and its quote must occur exactly in that input. Any malformed
response, safety block, exception, missing final output, or failed stage is an
abstention/no proposal. It cannot enter Candidate, Eligible Region, Score, source,
or Discord paths, and it has no external write/action tool.

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
and private identifiers are never emitted. It reports support/correctness for Evidence
Cards, usefulness against the human label, malformed/abstain and safe-stage-failure
rates, median latency, and Vertex response token totals. Cloud Billing—not this script—
is the cost source of truth.

## Human decision rule

Compare the three aggregate rows. The four-stage ADK path earns a follow-up only if it
materially improves evidence support/correctness and review usefulness over direct
Gemini without an unacceptable increase in abstention, safe failures, latency, or token
signal. A model result is never a policy decision; a human must review the aggregate
and underlying de-identified evaluation record before any private product work begins.
