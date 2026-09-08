# Career Command Centre private-workspace data contract

**Ticket:** [#28](https://github.com/n1tishc/kelsa-hunt/issues/28)
**Status:** accepted design contract; no private workspace data has been admitted yet.
**Applies to:** the one-owner, disposable Career Command Centre trial project only.

This contract makes the private workspace portable and reviewable without making it a
second Canonical Store. It is a boundary for the future IAP-protected workspace, not an
authorization to upload data. The admission gate in
[the trial foundation](trial-foundation.md) still applies: the owner must first verify
the Free Trial credit/expiry and retime the exit controls.

The public scanner remains the authority for public Records, Candidate, Eligible Region,
Score, source state, and Discord delivery. The private workspace is advisory: it never
writes back to those systems, applies, or contacts anyone.

## Contract rules

1. The owner is the authority for Career Profile facts, stated preferences, packet
   approval, and outcomes. Gemini output is derived advice, never a fact about the
   owner or a public job.
2. Every generated claim that says fit, gap, or tailoring must carry one or more
   Evidence Cards. A claim without one is retained and presented only as a suggestion.
3. Every retained private object has an opaque ID, `created_at`, `updated_at`, a schema
   version, and a deletion state. IDs must not contain names, employers, URLs, or
   profile text.
4. Deletion means removal from the application stores and the exported worklist. It
   does **not** promise erasure of Google-required audit metadata, service backups, or
   provider-side retention that the application cannot control. Those limits are
   explicit below.
5. The workspace stores a bounded, owner-selected working set. It may retain a full
   snapshot for a role the owner opens or shortlists; it must not bulk-copy the public
   Canonical Store or fetch/archive descriptions for every inbox row.

## Storage boundary and record shape

Firestore is authoritative for structured **private workspace** state, relationships,
owner decisions, and object manifests; it is never authority for a public Record or a
Derived View's public policy. Cloud Storage is authoritative only for immutable byte
objects: original uploads, selected-role description captures, generated files, and
export bundles. A Storage object is not a second database: every retained object has a
Firestore manifest with its digest, media type, byte length, creator, and deletion
state. The application must reject an object whose digest does not match its manifest.

Neither Cloud Run's filesystem, an ADK session, browser local storage, GitHub, Discord,
nor Cloud Logging holds authoritative private content.

| Object | Authority and provenance | Firestore / Storage shape | Mutability and correction | Retention, export, deletion |
| --- | --- | --- | --- | --- |
| **Career Profile** | Owner-entered resume facts, projects, history, notes, outcomes, and stated preferences. Imported files are evidence, not automatic truth. | Firestore holds normalized profile items and the active revision. Original resume/portfolio uploads live as immutable Storage artifacts linked by digest. | An owner edit creates a new profile-item revision and moves the active pointer; it never silently overwrites an earlier value. The owner can correct or delete any item. | Retain until owner deletion or trial exit. Export active items, prior revisions still referenced by packets, and linked artifacts. Delete Firestore revisions and Storage artifacts together after references are removed. |
| **Public Record reference** | The public Canonical Store is authoritative. The reference proves only which public Record was observed. | Firestore stores an opaque canonical UID or stable source URL, source name, observed time, and a content fingerprint/version if available. It stores no fetched board payload, candidate state, source state, or copied Record collection. | Immutable within a Selected Role Snapshot; a current-inbox reference may be refreshed or dropped. It cannot correct the public Record. | Unselected inbox references expire after 30 days or when closed and are not exported. References attached to a selected role export only as packet provenance. |
| **Selected Role Snapshot** | The owner opening or shortlisting a Record authorizes one on-demand capture. The source URL and capture time establish provenance; the captured description is the packet's evidence source, not a claim that the public posting remains live. | Firestore holds immutable capture metadata, Record reference, URL, time, retrieval status, digest, and a pointer to the captured description bytes in Storage. | Immutable. A later re-fetch creates a new snapshot; it cannot replace the earlier evidence basis. The owner may delete a snapshot and all dependent packets/artifacts. | Retain while a linked packet, outcome, or artifact remains. Export each selected snapshot and its manifest; delete both stores when no dependent object remains. Never create snapshots for unselected inbox rows. |
| **Relevant Profile Context** | A deterministic selection from cited Career Profile revisions for one pipeline run. It records what was actually supplied, not the entire profile by default. | Firestore stores the immutable manifest: pipeline run ID, ordered profile-item revision IDs, selection rationale/category, and content digests. It stores no second free-form copy when the referenced revision is sufficient. | Immutable. A rerun produces a fresh context manifest, even if it selects the same items. | Retain with its packet/run so Evidence Cards can be checked. Export manifests and every referenced historical profile revision; delete with the packet unless another packet references it. |
| **Fit Priority** | Gemini-derived advisory ordering from compact Record metadata, declared profile data, and optionally the Working Preference Model. It is not deterministic Score or Candidate status. | Firestore stores a versioned result: input reference IDs/digests, model/version, priority band, concise explanation, and generation time. | Replaceable current view, with prior versioned results retained only while an owner has shortlisted the role or a packet cites them. The owner can dismiss it; dismissal never changes public data. | Unselected/dismissed results expire after 30 days. Export only results tied to selected roles or outcomes; delete with their role workspace. |
| **Evidence Card** | A pipeline-produced support pointer to a Selected Role Snapshot span, Career Profile item revision, or explicit owner preference. The cited source is authoritative for the card's support; the card is not authority for the underlying fact. | Firestore holds immutable claim ID, support type, target ID, quote/span coordinates or item revision, target digest, and validation status. No duplicated full source document. | Immutable after packet review. A correction creates a superseding card/claim relation; unsupported cards are marked invalid rather than edited invisibly. | Retain with the packet/review history. Export alongside each packet and all referenced source/profile revisions. Delete when its packet is deleted. |
| **Application Studio packet and stage output** | Owner-reviewed advice produced by the bounded Role Analyst → Career Strategist → Application Writer → Evidence Critic pipeline. Approval is owner authority; model output is not. | Firestore stores structured stage products, packet metadata, evidence links, review state, and revision lineage. Downloadable resume/letter/checklist files live in Storage as immutable artifacts. | Generated stage products are immutable run outputs. Owner edits or approval create a new packet revision; the owner may mark a revision rejected. No stage can send, apply, or mutate public state. | Retain until owner deletes it or trial exit. Export all non-deleted packet revisions, structured stages, reviews, Evidence Cards, and referenced artifact bytes. |
| **Outcome** | Owner-entered application/interview/follow-up result and optional note. It is not inferred from a recruiter, ATS, or model. | Firestore stores an outcome revision, optional packet link, owner timestamp, and a small controlled vocabulary plus note. No outcome file is required. | Correctable by the owner. A correction appends a new outcome revision with a `supersedes` link; the current pointer changes and the earlier revision remains visible until deletion/export. | Retain until owner deletion or trial exit. Export the revision chain so learning is explainable; delete the chain on owner request. |
| **Working Preference Model** | Derived, inspectable personalization from explicit preferences, owner actions, and owner outcomes. It must never rewrite Career Profile facts or stated preferences. | Firestore stores an active model revision, inspectable weighted signals, source object IDs, confidence, and reset time. It contains no hidden-only state and no raw prompt/response transcript. | Replaceable and owner-resettable. Reset deletes the active derived model and signals, then starts empty; it does not alter source profile/outcome records. | Retain only while enabled. Export its active and historical inspectable revisions if the owner elects to keep learning history; otherwise exclude it and document the reset. Delete on reset or trial exit. |
| **Artifact** | Byte-level representation of an owner upload, selected job-description capture, generated packet file, or export. Provenance is its Firestore manifest and source object. | Storage is authoritative for bytes. Firestore manifest holds kind, digest, media type, length, creation actor, source object IDs, and retention/deletion state. | Immutable. A replacement is a new artifact and manifest, never an overwrite. | Retain only while referenced or explicitly kept by the owner. Export bytes under digest-addressed paths and verify checksums. Delete the object and manifest when unreferenced, subject to Cloud Storage soft-delete behavior. |
| **Operational trace** | Application-generated record that a bounded workflow was requested, validated, retried, or completed. It is not a packet, audit log, or model transcript. | Firestore stores immutable minimal metadata: opaque work ID, object IDs, stage name, model/version, schema-validation result, latency, token/cost counter if available, error class, and timestamps. | Immutable. A retry is a new linked trace. The trace never contains prompts, source text, model text, filenames, URLs, credentials, cookies, or profile/job content. | Retain for 30 days, except traces linked to a retained packet, where the minimal trace remains through packet retention. Export those packet-linked traces. Delete the application trace records at their expiry. |

The tables' retention periods are maximum application retention, not a legal hold. An
owner deletion request takes precedence except where another retained object still needs
a cited revision for reproducibility; in that case the workspace presents the dependent
objects and requires the owner to delete them together or explicitly retain them.

## Prompt, response, and logging policy

Raw model exchange is deliberately **not** a workspace record:

- Construct prompts in memory for a single request from the selected role snapshot and
  Relevant Profile Context. Do not use the full Career Profile as a standing system
  instruction.
- Do not persist raw prompts, raw provider responses, tool transcripts, chain-of-thought,
  request headers, access tokens, cookies, or browser content in Firestore, Storage,
  application logs, error reports, or the local exit archive.
- Validate the response against the stage schema in memory. Persist only the bounded,
  user-visible structured stage product needed by a packet, its Evidence Cards, and the
  minimal Operational Trace. Invalid/unparsed output is discarded after the request;
  its trace contains only the error class and schema-validation result.
- Cloud Logging may contain the minimal Operational Trace fields needed to operate the
  service. Log labels and exception messages must be scrubbed so they cannot carry
  supplied content. The application must not log request/response bodies.
- Keep provider caching/session features disabled unless a later ticket documents their
  retention effect and the owner explicitly accepts it. Gemini Live session resumption
  is out of scope for the trial.

Vertex AI states that managed models do not use customer data to train or fine-tune
models without permission/instruction, but that is not an application-controlled
[zero-retention guarantee](https://cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention).
Cloud Logging's `_Required` Admin Activity and System Event audit logs retain for 400
days and cannot be deleted or changed. Consequently, never put private text into
resource names, log labels, audit-relevant request fields, or metadata that may reach
required audit logs. The trial's day-80 deletion completes the application-data deletion
plan; it cannot erase that required operational metadata. [Cloud Logging retention](https://cloud.google.com/logging/docs/store-log-entries)
describes that non-deletable limitation.

## Local exit archive

The local archive is a versioned, encrypted directory or encrypted archive created by
the owner outside the trial project. It is the only intended retained copy after the
project is deleted. It must be self-describing and verifiable without a running Cloud
service:

```text
career-command-centre-export-v1/
  README.md                 archive format, restore instructions, known retention limits
  manifest.json             archive version, export time, object inventory, SHA-256 hashes
  firestore.ndjson          private structured documents, including revision links
  artifacts/<sha256>        immutable selected snapshots, uploads, packet files
  checksums.sha256          byte-level verification list
  deletion-worklist.md      Cloud objects/accounts still to remove and completion evidence
```

`firestore.ndjson` contains only documents permitted by this contract. Artifact paths are
digest-addressed; a manifest maps them to their Firestore object IDs and media types.
The export program must verify every artifact digest, referential integrity (Evidence
Card targets, context revisions, packet/artifact links), schema versions, and count of
exported non-deleted documents before declaring success. A rehearsal restore must open a
packet, resolve each Evidence Card, read its selected source span, and confirm that an
outcome's revision chain is intelligible.

The archive deliberately excludes:

- `jobs.json`, `sources.json`, the public Canonical Store, source payloads, and scanner
  run history;
- all unselected Smart Inbox rows and their compact Record references;
- any bulk job-description cache, board crawl result, Candidate/Score/Discord state; and
- raw prompts, raw model responses, Cloud Logging exports, credentials, and billing or
  infrastructure secrets.

A selected role's single snapshot and its compact Record reference are included because
they are evidence for an owner-created packet, not a private mirror of public Records.
If a public URL no longer resolves, the snapshot's capture timestamp and digest make the
past advisory packet still reviewable without attempting to reconstitute the public
store.

## Export and deletion sequence

1. At the day-75 rehearsal, stop nonessential enrichment; export Firestore and all
   contract-eligible artifact objects; build and checksum the local archive; perform the
   representative restore; and record any unresolved references in the deletion
   worklist.
2. At day 80, pause the Scheduler, revoke deployment/runtime access and secrets, and
   verify that no route can call Vertex before final export. Do not rely on a budget
   alert as a hard shutdown.
3. Delete application documents and artifacts after the local archive verifies. Cloud
   Storage soft delete can retain recoverable object copies for its configured period;
   it must be understood and allowed to expire before claiming byte deletion is final.
4. Delete the Firestore database/bucket and then the dedicated trial project according
   to the approved shutdown plan. Record the unavoidable Cloud audit-log retention limit
   in the archive README rather than claiming total erasure.

This contract constrains future implementation. A new schema, storage location, logging
sink, model feature, or retention exception that weakens any listed boundary requires an
explicit contract revision before private data is admitted.
