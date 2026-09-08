# Owner-triggered role snapshots and profile context

**Ticket:** [#32](https://github.com/n1tishc/kelsa-hunt/issues/32)
**Status:** implementation seam complete; private-data admission and deployment remain
blocked by the owner’s Ticket #27 trial facts.

The Smart Inbox has no description-fetch path. Its public Store read remains a
read-only Candidate-derived view. A description request can occur only through the
authenticated owner’s `POST /roles/{uid}/open` or
`POST /roles/{uid}/shortlist` action, after the role has been confirmed in the current
inbox. There is no scheduled route, scanner import, or SmartRecruiters board-detail
fan-out in this workspace code.

The action creates one immutable `SelectedRoleSnapshot` per selected Record. It records
only the public Record UID/reference, HTTPS source URL, capture time, description digest,
and captured description; an existing snapshot is reused on a later shortlist action,
so it is not silently re-fetched. The owner sees the source provenance and a bounded
`RelevantProfileContext` listing the specific profile-item revisions used for that role.

The current `InMemoryRoleWorkspace` is deliberately a test/preview adapter, not a
production data store. It receives only synthetic test profile items in this repository.
It is never constructed by the production environment entrypoint, so a production
request remains safely blocked rather than fetching or retaining a description before
the Ticket #27 admission facts are verified. A later persistence adapter must conform to
the Firestore/Storage manifest, immutability, retention, and export rules in
[the private-workspace data contract](private-workspace-data-contract.md); it must never
copy the Canonical Store or bulk-fetch descriptions.
