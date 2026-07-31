# Enforce one strict-US location policy

<!-- wayfinder:domain-modeling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Claimed by

Codex `/root` with the user, 2026-07-31.

## Question

How does one shared predicate enforce the decided US eligibility boundary across
notifications, dashboard builds, queries, and exports without destroying source data?

The dashboard prototype exposed that the Canonical Store contains foreign Records by
design while the visible archive had no location filter. The existing notification
predicate is also too permissive: it assumes a bare `Remote` location is domestic and
uses a short foreign-marker blacklist.

The settled behavior is:

- Include a Record only when at least one location has explicit US evidence: `US`, `USA`,
  `United States`, a US state/territory, or a recognized US locality.
- Exclude bare `Remote`, global, unknown, and foreign-only locations.
- Include a mixed-location Record if it has a US option, but expose only its US locations
  in Derived Views.
- Preserve the source's complete location list in the Canonical Store.
- Apply the same predicate to Discord Candidates and every user-visible Derived View.

Implementation must use one production predicate rather than copying the throwaway
prototype's heuristic. Cover country tokens, every state/territory and postal
abbreviation, common source delimiters, mixed-country postings, and ambiguous strings
with table-driven tests. Ambiguity fails closed.

## Discovered from

- [Prototype the dashboard and decide how it gets its data](10-dashboard-shape.md)

## Related work

- [Re-tune the notification threshold and age gate](04-threshold-and-age-gate.md)
