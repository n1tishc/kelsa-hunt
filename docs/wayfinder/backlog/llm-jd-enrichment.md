# Backlog: LLM enrichment pass over job descriptions

<!-- wayfinder:backlog -->

**Filed:** 2026-08-03. **Not on any map.** This is deliberately *not* a ticket on
[the UK map](../uk-expansion/map.md) — it sits beyond that destination and must not be pulled
into the UK work. Promote it to its own effort only after UK roles are live.

## The idea

Add a model call that reads the **job description** and judges what title-only regexes
structurally cannot: real seniority, sponsorship willingness, and whether a UK grad scheme is
actually an engineering role.

## Why it exists

`classify()` is six regexes over the **title only** — `CONTEXT.md` documents this as a
permanent, accepted limitation, not a bug (see the MTS entry: seniority lives in the JD's
years-of-experience line, which `classify()` never reads). Every brittleness found while
charting the UK map traces to that one root cause:

| Failure | Score today | Why |
| --- | --- | --- |
| `Analyst Programmer` | 0 | UK-common title, no US analogue, fails `ROLE_MATCH` |
| `Technology Graduate Scheme` | 0 | no "scheme"/"programme" vocabulary |
| `Software Engineer - L3 Support` | 5 | `l3\b` reads as a new-grad rung; it's a support tier |
| senior MTS reqs | 5 | deliberately accepted noise — the JD holds the seniority signal |

A model reading the JD gets all four right.

## What was already verified (2026-08-03) — don't re-derive

- **The JD text is available with no extra request.** Greenhouse serves it on the endpoint
  `fetch_greenhouse()` already calls, behind a flag:
  `boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true`. Observed on `graphcore`: the
  sample JD is **5,898 chars ≈ 1,475 tokens**. The flagged response also carries `education`,
  `application_deadline`, and `first_published` — `application_deadline` is directly relevant to
  the UK map's *grad-scheme deadlines* fog. **Only Greenhouse was checked**; Ashby, Lever, and
  SmartRecruiters each need their own verification.
- **No new infrastructure is needed, and no VPS.** The model is a hosted API call, not something
  to self-host — a cheap VPS has no GPU, and a model small enough to run on one would be worse at
  this than the current regexes. GitHub Actions already provides the compute; the key is an
  Actions secret exactly like `DISCORD_WEBHOOK`. Note **fork PRs do not receive secrets**, so an
  enrichment step would skip on outside PRs.
- **Cost, on measured tokens.** Enriching only Band 3/5 candidates at ~50 JDs/day
  (~75k input tokens/day): roughly **$2/mo** on Haiku 4.5 ($1/MTok in), **~$7/mo** on Sonnet 5
  ($3, $2 intro through 2026-08-31), **~$11/mo** on Opus 5 ($5). Two levers cut it further and
  both fit this architecture well:
  - **Prompt caching** — the rubric is byte-identical across every posting, so it caches; reads
    are ~0.1× base. Opus 5's minimum cacheable prefix is 512 tokens.
  - **Batches API, 50% off** — completes within an hour, which suits the Band 3 *manual sweep*
    and a retroactive pass over all 24,650 Records, but is too slow for the 30-minute notify
    cadence. Batch the sweep; call live only for new candidates.

## The tension to resolve before building

**Pattern matching buys a property that is easy to undervalue: scoring is free, so re-scoring is
retroactive over all 24,650 stored Records at zero cost.** That's what lets any rule change be
validated against full history, and it's why the tool runs every 30 minutes on free Actions
minutes from a public repo with no server. A per-posting model call ends that property. So the
shape almost certainly is:

- Regexes stay the **cheap, retroactive, free** first pass over everything.
- The model is an **enrichment pass on Band 3/5 candidates only** — never on all 25k.
- The verdict is **persisted** on the Record, so it isn't re-paid on every scan. That collides
  with `CONTEXT.md`'s rule that Score is computed at query time and never persisted as the source
  of truth — reconcile that deliberately, don't drift into it.

## Open questions

- Does the model's verdict gate notification, adjust Score, or only annotate? A gate would be the
  tool's first **suppressive** filter, reversing "a duplicate notification is preferred to
  suppressing a real requisition."
- Where does the verdict live, given Score is query-time by design and `jobs.json` is the binding
  resource under a 20 MiB warning gate (currently 10.6 MiB)?
- Do the other five adapters expose JD text at all? If not, enrichment is Greenhouse-only and the
  Score becomes inconsistent across sources.
- Does the repo stay stdlib-only? The `anthropic` SDK would be its first third-party dependency —
  `.venv` currently contains only `pip`.

## If it ever grows past a single call

An agent that tailors a CV, drafts a cover letter, or tracks application state is a different
shape and would want a harness. Still no VPS: **Managed Agents** hosts both the agent loop and a
per-session sandbox, and its **scheduled deployments** run on cron server-side — which would
replace the Actions cron and fix its documented best-effort imprecision. Evaluate that before
buying a server.

## Separately: what a VPS would actually buy

Judged on its own merits, not as a model host — four real things, none of which is the model:
cron precision (Actions cron is best-effort, per `HANDOFF.md`); a **private repo** (ADR-0001 keeps
it public purely for unmetered minutes, so a VPS dissolves that constraint and would let
`annotations.json` be committed); a real backend for the ledger, which is a static Pages artifact
today; and long-running state beyond a single-file JSON store. Buy it for those, not for this.
