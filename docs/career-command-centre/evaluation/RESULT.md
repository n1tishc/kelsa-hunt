# Evaluation decision status

**Ticket:** [#30](https://github.com/n1tishc/kelsa-hunt/issues/30)
**Status:** implementation ready; Vertex comparison intentionally **not admitted**.

Ticket #27's foundation fact sheet records that the exact Free Trial credit/expiry and
the corresponding day-75/day-80 dates still require owner verification. Its admission
gate expressly prevents Ticket #30 from beginning until that fact is recorded. The
evaluator therefore refuses a Vertex call unless the owner supplies a local, untracked
admission-facts file and explicitly opts in at the command line.

No result is claimed yet. In particular, no comparison of ADK and direct Gemini is
decision-quality until the gate is opened and a human reviews the aggregate-only report.
The evaluator is designed to fail closed: a malformed stage, missing evidence, invalid
corpus, or absent admission fact produces no advisory proposal and no public-system
action.

Once admitted, record only the aggregate table here: valid packets, abstentions,
Evidence Card support/correctness, human review usefulness, stage-specific failures,
latency, and token/cost signals. Do not add the raw corpus, prompts, responses,
credentials, project ID, or private profile material to this repository.
