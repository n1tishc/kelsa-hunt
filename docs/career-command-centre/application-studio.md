# Evidence-backed Application Studio

**Ticket:** [#33](https://github.com/n1tishc/kelsa-hunt/issues/33)
**Status:** bounded in-memory implementation seam complete; production admission and
durable private storage remain blocked by the trial foundation.

For an owner-selected role, the Application Studio runs four fixed advisory stages in
order: Role Analyst, Career Strategist, Application Writer, and Evidence Critic. Each
stage returns only a small structured result. The owner can inspect every result, see
the bounded Selected Role Snapshot and Relevant Profile Context that were supplied, run
another packet, edit its draft, and mark that draft reviewed.

Fit, gap, and tailored-material claims are not trusted merely because a model returned
them. Every supplied Evidence Card is checked locally against either the selected role
snapshot or one specific selected profile-item revision. A valid card records its source
object, digest, and exact quote. Any unsupported claim is visibly retained only as a
**Suggestion**. A missing, unavailable, or malformed stage is shown as such with no
claims, so the owner can still review the rest of the packet safely.

The preview has no external tools, scanner writes, Discord path, application submission,
outreach, or notification action. The production entrypoint does not construct either a
role workspace or Application Studio. `VertexStageRunner` is a direct, four-call Gemini
Flash adapter with JSON-schema output and no tools; it is intentionally unconstructed
until the Ticket #27 admission facts and a durable Firestore/Storage adapter are in
place. It retains neither raw prompts nor provider responses.

The in-memory adapter exists only for tests and a synthetic preview. It must be replaced
with the contract's immutable packet/evidence manifests and owner revision lineage
before real selected snapshots or Career Profile context are admitted.
