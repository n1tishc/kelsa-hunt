# kelsa-hunt

A personal Bay Area new-grad/entry-level SWE + MLE job alerter. Fetches postings from Simplify plus configured Greenhouse/Lever boards, keeps every record it has ever seen, and pings Discord about the ones worth looking at.

## Language

**Record**:
A single job posting as fetched from a source, keyed by `uid`. Stored permanently once seen, regardless of whether it currently matches any filter.
_Avoid_: Listing, posting (when referring to the stored object specifically)

**Score**:
A 0/3/5/10 rating `classify()` assigns a Record's title (and degree requirements) expressing how confident the match is. Computed at query time from the stored title, never persisted as the source of truth — so re-scoring after a rule change is retroactive over full history.
_Avoid_: Rank, weight

**Score Band**:
The three tiers `classify()` produces: **10** (explicit new-grad wording), **5** (junior-level marker, e.g. "Engineer I", MTS), **3** (bachelors-eligible with no other signal — the "maybe" tier).

**Notification Threshold**:
The `--min-score` a Record's Score must clear to be pushed to Discord. Decided default posture: **storage is recall-first** (every Record is kept no matter its Score), **notification is precision-first with some tolerated noise** — default threshold sits at Score Band 5, admitting junior-marker matches alongside explicit new-grad ones, while Band 3 stays a manual `query --min-score 3` sweep rather than an auto-notify tier.

**Bay Area** (location scope):
The `BAY_TERMS` city list (SF plus peninsula/south-bay/east-bay: San Jose, Mountain View, Palo Alto, Sunnyvale, Oakland, Berkeley, etc.) — additions to this are data changes, not design decisions. Remote is in-scope by an **exclusionary** rule, not an inclusionary one: a bare `"Remote"` string with no country/state qualifier at all is treated as in-scope (assumed domestic, since fully-global remote reqs almost always say "Remote (Global)" or name eligible countries explicitly), and only an *explicit* foreign/regional marker (EMEA, APAC, Canada, India, UK, LatAm, Ireland, Germany) knocks a listing out. Decided deliberately over the inclusionary alternative (require an explicit "US" string) because ATS postings frequently omit "US" on domestic-only remote roles, and requiring it would silently drop legitimate matches.

**MTS (Member of Technical Staff)**:
The generic IC title used by SF AI labs (e.g. Anthropic, one of the configured Greenhouse sources) at *every* seniority level, not just entry-level — the seniority signal lives in the job description (years of experience), which `classify()` never reads (title-only). Because there is no title-only way to separate a junior MTS req from a senior one, the classifier deliberately treats **any** MTS title as a junior-positive signal (+5) and accepts the resulting noise (occasional senior MTS pings), since the alternative — gating or dropping the bonus — would guarantee missing genuine entry-level lab roles rather than just occasionally over-including senior ones. This is a permanent, accepted limitation of title-only classification, not a bug to fix later.

**Leveling scheme (L3/E3 vs L4+/E4+)**:
`classify()` assumes the Google/Meta-style convention where **L3 / E3 / IC1 / T1** is the new-grad rung (junior-positive, +5) and **L4+ / E4+** is a hard, permanent reject (score forced to 0 — excluded from ever becoming a Candidate at any threshold, not merely down-scored). Decided to keep as a hard reject rather than hedge against non-standard leveling at other companies: confirmed none of the current `sources.json` companies are known to number their new-grad rung as L4+/E4+, and softening the rule now would reintroduce the mid-level noise it exists to prevent. If a future source turns out to use different numbering, that's a fix-when-noticed problem, not something to pre-hedge.

**Cross-post** (vs. distinct req):
Two Records naming the same real-world opening, reached via different sources (e.g. the same Stripe role appearing via Simplify and via Stripe's own Greenhouse board). Distinct from two separate reqs that merely share a company/title/location. Dedup should collapse the former, never the latter.

**Closed** (Record state):
Marks a Record no longer listed by the source it was found through — not a claim the role is filled. Source-scoped and reversible: a Record automatically un-closes the moment any source reports it live again. Records are never pruned once closed; the store is a permanent historical ledger.

**Candidate**:
A Record that currently passes `Store.candidates()` — i.e. it clears the Notification Threshold, is Bay Area, isn't closed, and (usually) hasn't been notified yet. A Candidate is a filtered *view* over Records, not a stored state.
_Avoid_: Match (ambiguous with the general English sense)
