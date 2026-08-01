# kelsa-hunt

A personal US-scoped new-grad/entry-level SWE + MLE job alerter. Fetches Records
from Simplify, Ambicuity, and configured Greenhouse, Lever, Ashby,
SmartRecruiters, Workable, and Recruitee boards; keeps every Record it has ever
seen; presents a strict-US public ledger; and pings Discord about the ones worth
looking at.

## Language

**Record**:
A single job posting as fetched from a source, keyed by `uid`. Stored permanently once seen, regardless of whether it currently matches any filter.
_Avoid_: Listing, posting (when referring to the stored object specifically)

**Canonical Store**:
The authoritative, permanent public ledger of every Record the system has seen. Other
representations—such as dashboard data, exports, and reports—are Derived Views that can
always be regenerated from the Canonical Store and never become competing sources of
truth.

**Derived View**:
A disposable representation computed from the Canonical Store for a particular use,
such as browsing or analysis. It may contain only a subset or a reshaping of Records,
but it owns no state and can be deleted and rebuilt without information loss.

**Public Job Ledger**:
The read-only GitHub Pages Derived View built from the Canonical Store after a meaningful
Store change. It exposes only allowlisted public fields and strict-US locations. It never
contains private application annotations and is not committed back to the repository.

**Source Inventory**:
The configured board/feed entries in `sources.json`, plus the built-in Simplify feed.
Adding an entry increases coverage; removing or editing an entry changes configuration
but never deletes historical Records from the Canonical Store.

**Expansion Gate**:
The growth guardrail state that prevents an increase in Source Inventory after the
Canonical Store, round-trip timing, or packed Git history reaches a hard limit. It does
not stop existing Source Fetches, notifications, persistence, or dashboard deployment,
and it never migrates or prunes Records automatically.

**Score**:
A 0/3/5/10 rating `classify()` assigns a Record's title (and degree requirements) expressing how confident the match is. Computed at query time from the stored title, never persisted as the source of truth — so re-scoring after a rule change is retroactive over full history.
_Avoid_: Rank, weight

**Score Band**:
The three tiers `classify()` produces: **10** (explicit new-grad wording), **5** (junior-level marker, e.g. "Engineer I", MTS), **3** (bachelors-eligible with no other signal — the "maybe" tier).

**Notification Threshold**:
The `--min-score` a Record's Score must clear to be pushed to Discord. Decided default posture: **storage is recall-first** (every Record is kept no matter its Score), **notification is precision-first with some tolerated noise** — default threshold sits at Score Band 5, admitting junior-marker matches alongside explicit new-grad ones, while Band 3 stays a manual `query --min-score 3` sweep rather than an auto-notify tier.

**Notification Batch**:
The newly eligible Cross-post Groups produced by one scan and awaiting
Discord delivery. Volume may change how the Batch is presented, but no Candidate leaves
it until delivery succeeds.

**Freshness Timestamp**:
The best source-provided activity timestamp used by the notification age gate, with
`first_seen` as fallback when a source provides none. It may mean published, created,
or last updated depending on the source; it is not uniformly an original-posting date.

**US eligibility boundary** (location scope):
Every user-visible Derived View and every notification fails closed on country: a Record
must have explicit US evidence (`US`, `USA`, `United States`, a US state/territory, or a
recognized US locality). Bare `Remote`, global, unknown, and foreign-only locations are
out of scope. A multi-location posting remains eligible when at least one location is in
the US, but the Derived View displays only its US locations; the Canonical Store retains
the source's complete location list. This replaces the earlier permissive assumption that
an unqualified `Remote` location was domestic.

**Bay Area** (notification-locality scope):
The `BAY_TERMS` city list (SF plus peninsula/south-bay/east-bay: San Jose, Mountain View,
Palo Alto, Sunnyvale, Oakland, Berkeley, etc.) — additions to this are data changes, not
design decisions. Local notifications still use this narrower area; remote notifications
must also satisfy the US eligibility boundary above.

**MTS (Member of Technical Staff)**:
The generic IC title used by SF AI labs (e.g. Anthropic, one of the configured Greenhouse sources) at *every* seniority level, not just entry-level — the seniority signal lives in the job description (years of experience), which `classify()` never reads (title-only). Because there is no title-only way to separate a junior MTS req from a senior one, the classifier deliberately treats **any** MTS title as a junior-positive signal (+5) and accepts the resulting noise (occasional senior MTS pings), since the alternative — gating or dropping the bonus — would guarantee missing genuine entry-level lab roles rather than just occasionally over-including senior ones. This is a permanent, accepted limitation of title-only classification, not a bug to fix later.

**Leveling scheme (L3/E3 vs L4+/E4+)**:
`classify()` assumes the Google/Meta-style convention where **L3 / E3 / IC1 / T1** is the new-grad rung (junior-positive, +5) and **L4+ / E4+** is a hard, permanent reject (score forced to 0 — excluded from ever becoming a Candidate at any threshold, not merely down-scored). Decided to keep as a hard reject rather than hedge against non-standard leveling at other companies: confirmed none of the current `sources.json` companies are known to number their new-grad rung as L4+/E4+, and softening the rule now would reintroduce the mid-level noise it exists to prevent. If a future source turns out to use different numbering, that's a fix-when-noticed problem, not something to pre-hedge.

**Cross-post** (vs. distinct req):
Two Records naming the same real-world opening, reached via different sources (e.g. the same Stripe role appearing via Simplify and via Stripe's own Greenhouse board). Distinct from two separate reqs that merely share a company/title/location. Dedup should collapse the former, never the latter.
When a shared opening identity cannot be proven, Records remain distinct; a duplicate
notification is preferred to suppressing a real requisition.

**Opening Identity**:
The stable identity an external hiring system assigns to one real-world opening,
scoped to its platform and employer or tenant where necessary. Company display names,
title similarity, and location similarity are not Opening Identity.

**Cross-post Group**:
A Derived View of source-specific Records that share a proven Opening Identity. The
group is live if any member is live and notified if any member has been notified;
Canonical Records remain separate and unchanged.

**Closed** (Record state):
Marks a Record no longer listed by the source it was found through — not a claim the role is filled. Source-scoped and reversible: a Record automatically un-closes the moment any source reports it live again. Records are never pruned once closed; the store is a permanent historical ledger.

**Source Fetch**:
One attempt to observe the current Records published by one configured source. A
healthy Source Fetch provides evidence for both live and newly Closed Records from
that source. An unhealthy Source Fetch—transport failure, invalid data, or an
unexpected transition from a previously non-empty source to zero Records—provides no
closure evidence. Failures are isolated: they never imply that another source failed
and never mark the failed source's Records Closed.

**Candidate**:
A Record that currently passes `Store.candidates()` — i.e. it clears the Notification
Threshold, is either Bay Area or explicitly US-remote, isn't closed, satisfies the age
gate, and (usually) hasn't been notified yet. A Candidate is a filtered *view* over
Records, not a stored state.
_Avoid_: Match (ambiguous with the general English sense)
