# Decide how a Record is identified across many sources

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

What makes two Records the same real-world opening once the tool pulls from dozens of
sources instead of four?

`CONTEXT.md` already draws the line: a **Cross-post** is two Records naming the same
opening reached via different sources, and it must collapse — while two genuinely distinct
reqs sharing company/title/location must not. Today's `dedup()` implements that with a
Greenhouse job id scraped from the URL when available, else a fuzzy
`(company, normalized title, first location)` key.

That fallback degrades badly at scale:

- `company` is derived from the board slug via `slug.replace("-", " ").title()`, so the
  same employer appears as different strings depending on which source found it — the
  fuzzy key silently fails to match exactly when it's needed most.
- Only `locations[0]` participates, so multi-location reqs collapse or don't by accident.
- There's no equivalent of `extract_gh_id` for Lever, Ashby, or any new platform.

Settle: whether company identity needs a canonical mapping rather than slug-derived
strings; whether per-platform id extraction should be generalised; and what the tolerance
is for over-collapsing (a real role lost) versus under-collapsing (duplicate pings) — they
are not symmetric costs and the current code doesn't say which it prefers.

## Resolution

Resolved with the user on 2026-07-31. Prefer under-collapsing: a duplicate notification
is acceptable; suppressing a distinct requisition is not.

The current fuzzy fallback must be removed. Across 12,918 Records it creates 778
multi-Record groups containing 2,106 Records, but zero of those groups span sources.
Many are demonstrably different requisitions—for example, 29 Huntington Workday roles,
27 Jerry Ashby roles, and 24 Palo Alto Networks Workday roles with different external
IDs. It provides no measured cross-source benefit while violating the distinction
between a Cross-post and a distinct req.

Use these rules instead:

- Canonical Records remain source-specific and keyed by their source `uid`. Dedup is a
  query-time Derived View; it never merges or rewrites the Canonical Store.
- A Cross-post Group forms only when Records share a proven Opening Identity. Resolve
  identity from structured source IDs first and recognized destination URL shapes
  second, using an explicit registry for Greenhouse, Lever, Ashby, Workday,
  SmartRecruiters, Workable, and Recruitee.
- Scope external IDs by platform and employer/tenant when the platform's identifiers
  require it. Company display names are presentation data, not identity, and there is
  no manually maintained company-alias map.
- Unknown/custom URLs and unparseable Records are singleton groups. Do not use generic
  URL equality, normalized company/title/location, or title similarity as production
  identity evidence.
- A Cross-post Group is live when any member is live and notified when any member has a
  `notified_at` value. A proven Cross-post discovered after its sibling was notified does
  not notify again. Successful delivery stamps every current member.
- Candidate eligibility is satisfied when any live member qualifies. Select one
  representative deterministically by highest Score, then newest Freshness Timestamp,
  then stable `uid`; display that Record's strict-US Derived View rather than fabricating
  a merged Canonical Record.

Implementation fixtures must prove that wrappers for the same external requisition
collapse, different Workday/Ashby requisition IDs with identical company/title/location
remain distinct, identical ID tokens under different tenant scopes remain distinct, and
unknown platforms fail open as separate Records. Re-run the pinned Ambicuity/Simplify
overlap measurement when implementing its fetcher; this resolution clears that fetcher's
identity gate but does not itself add the source.

## Blocked by

- [Find aggregator feeds worth adding beyond Simplify](07-aggregator-feeds.md) — the
  overlap numbers that ticket produces are the actual duplicate load to design against.
- [Fix the two ways notifications get lost silently](03-fix-notification-loss.md) — the
  dedup/notify interaction is being changed there; decide identity on top of the fixed
  behaviour, not the broken one.
