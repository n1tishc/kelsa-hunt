# Evaluation decision status

**Ticket:** [#30](https://github.com/n1tishc/kelsa-hunt/issues/30)
**Status:** direct-only synthetic Vertex evaluation completed 2026-08-15; the
workflow is promising for further synthetic refinement, but not admitted for private
data or deployment.

Ticket #27's owner-verifiable admission record was complete before this run. The
evaluator used a frozen, de-identified ten-example corpus and `gemini-2.5-flash` in
`us-central1`, with no tools and aggregate-only batch reports. No Career Profile, real
job description, public Store content, packet, or source was sent to Vertex.

| Comparator | Valid recommendations | Safe abstentions | Locally rejected recommendations | Prompt / output tokens |
| --- | ---: | ---: | ---: | ---: |
| Deterministic metadata baseline | 0/10 | 10/10 | 0/10 | 0 / 0 |
| Direct Vertex structured call | 7/10 | 1/10 | 2/10 | 2,218 / 1,829 |

Every accepted recommendation selected only human-approved, stable evidence IDs, so
its evidence-support and evidence-correctness rates were both 1.0. The two rejected
outputs attempted to recommend mismatched roles with unapproved evidence IDs; the
deterministic gate withheld both packets. One remaining mismatch safely abstained.
No stage/runtime failure occurred. Across the five two-example batches, median request
latency ranged from 5,545 to 6,455 ms.

**Decision:** retain the direct Vertex plus deterministic evidence-ID gate for the
next synthetic iteration; do not use the deprecated ADK sequential path. Before any
private-workspace admission, add a held-out de-identified corpus and evaluate
human-reviewed usefulness separately from evidence selection. Real private data,
durable private persistence, and deployment remain blocked.

The aggregate batch reports remain only in the local temporary workspace. Do not add
their raw JSON, corpus, prompts, responses, credentials, project ID, or private
profile material to this repository.
