# Prototype the dashboard and decide how it gets its data

<!-- wayfinder:prototype -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

What does the hosted page look like, and how does it read the store?

A public HTML page in the repo showing everything the tool has seen — browsable and
filterable. Constraint already locked on the map: **job data only, never applied state**,
since the repo is public per ADR-0001.

The data path is the real decision and it's coupled to whatever
[Decide the committed store's shape](01-committed-store-shape.md) settles:

- Client-side fetch of the store — simplest, but a 6.5 MB download on every page load and
  growing, which is likely disqualifying on its own
- A pre-rendered static page built by the workflow — fast to load, but adds another
  committed artifact churning per run, i.e. more of the exact problem ticket 01 exists for
- A slimmed derived JSON (open + recent only) fetched client-side, with the full store
  left as the archive
- Something else the store-shape decision makes obvious

Also settle through the prototype: default view (open Bay Area matches? everything?), which
filters earn their place (score band, company, source, open/closed, age), whether closed
Records are visible at all, and how GitHub Pages gets published from this repo.

**Make something rough and react to it** — the point is raising fidelity, not shipping.
Link the prototype from this ticket rather than pasting it in.

## Prototype

[Complete job-ledger prototype](../prototypes/job-ledger-prototype/)

Run from the repository root:

```sh
python3 docs/wayfinder/prototypes/job-ledger-prototype/server.py
```

Then open <http://127.0.0.1:8765/?variant=A>. Use the floating arrows or the keyboard
arrow keys to compare:

- A — spreadsheet ledger
- B — archive inspector
- C — market timeline

This is deliberately throwaway UI. It reads the real `jobs.json` through a derived,
read-only endpoint; it does not modify the Canonical Store or create another committed
data store.

## Prototype feedback

- Variant A (spreadsheet ledger) is the preferred primary shape: simple is appropriate
  for a single-user tool.
- The first real-data pass exposed an unwanted behavior: the complete archive includes
  foreign locations. The visible archive and notifications must be US-only.
- An unqualified `Remote` location is excluded. A role needs explicit US evidence
  (`US`, `USA`, `United States`, a US state/territory, or a recognized US locality);
  ambiguous locations fail closed.
- A mixed-location posting stays visible when it has at least one US location, but its
  Derived View displays only the US locations. Production enforcement is tracked in
  [Enforce one strict-US location policy](14-enforce-us-location-eligibility.md).
- The ledger opens on currently open US Records. Complete history remains available
  through the status filter.
- The default Score filter is `3+` (plausible entry-level), with `5+`, `10+`, all Scores,
  and unclassified Records available in the same control.
- GitHub Actions generates the compact US-only JSON and static dashboard as an ephemeral
  Pages deployment artifact after a meaningful Canonical Store change. Neither artifact
  is committed, and a no-change scan does not redeploy Pages.

## Resolution

Resolved with the user on 2026-07-30.

Ship the spreadsheet-ledger shape represented by variant A. It is a read-only personal
archive over job data, with application state excluded. The initial view is open,
explicitly US-eligible Records at Score `3+`; complete history and every Score remain
available through filters. Search covers company, role, and location, accompanied by
status, source, and Score controls. Historical rows retain posted, first-seen, and
closed-at dates.

The Canonical Store remains the sole committed data source. On meaningful store changes,
Actions applies the shared strict-US location policy, builds a compact Derived View and
the static page, and deploys them together as a Pages artifact. No dashboard or derived
JSON is committed. Variant B's inspector and variant C's analytics do not enter the first
version; they can be reconsidered only if actual use exposes a need.

## Blocked by

- [Decide the committed store's shape](01-committed-store-shape.md)
