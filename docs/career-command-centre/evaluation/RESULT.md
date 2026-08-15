# Evaluation decision status

**Ticket:** [#30](https://github.com/n1tishc/kelsa-hunt/issues/30)
**Status:** synthetic Vertex comparison completed 2026-08-15; neither model path
earned private-workspace admission.

Ticket #27's owner-verifiable admission record was complete before this run. The
evaluator used only the frozen, de-identified three-example corpus, the selected
`gemini-2.5-flash` model in `us-central1`, no tools, and an aggregate-only local report.
No Career Profile, real job description, public Store content, packet, or source was
sent to Vertex.

| Comparator | Valid packets | Abstentions | Invalid / malformed | Median latency | Prompt / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Deterministic metadata baseline | 0/3 | 3/3 | 0/3 | 0 ms | 0 / 0 |
| Direct Vertex structured call | 0/3 | 3/3 | 2/3 | 7,491 ms | 364 / 753 |
| Four-stage ADK no-tools pipeline | 0/3 | 3/3 | 2/3 | 27,247 ms | 4,070 / 913 |

The direct and ADK paths each produced two locally rejected Evidence Card responses;
the remaining example abstained. The ADK stages themselves completed, but produced no
locally valid proposal. Evidence support, evidence correctness, and review usefulness
were all 0.0 for both model comparators. The report contains no raw corpus, prompt, or
model response.

**Decision:** do not admit real private data or deploy this evaluator. The fixed ADK
path is slower and uses substantially more prompt tokens without improving a valid-packet
outcome. If this experiment continues, refine the de-identified corpus/label protocol
and test the direct, deterministic-validation path only; retain the fail-closed gate.

The aggregate report remains only in the local temporary workspace. Do not add its raw
JSON, corpus, prompts, responses, credentials, project ID, or private profile material
to this repository.
