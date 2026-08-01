# Target company list and verified board identifiers

**Research date:** 2026-07-30
**Result:** 107 verified candidate employers: **105** have non-empty public boards
that the current fetchers can consume (73 Greenhouse, 1 Lever, 31 Ashby); **2** have
live direct boards but need a future fetcher. This intentionally contains no guessed
slug.

## Method and meaning of “verified”

For every supported entry below, I made a live, unauthenticated request to its exact
endpoint on 2026-07-30 and counted the returned records. Greenhouse counts are the
length of `jobs`; Lever counts are the response-array length; Ashby counts only jobs
whose `isListed` is not `false`. Thus “N jobs” means the board was both reachable and
non-empty at that instant, **not** that it had a Bay-Area, new-grad SWE/MLE role at
that instant. The latter is deliberately left to Kelsa-Hunt’s normal storage and
classifier filters.

“Bay Area employer” here means a company with a Bay Area headquarters or material
engineering presence (and, for a few large multi-city employers, a Bay Area hiring
presence). The list is biased to product/infra/AI/fintech employers where entry-level
SWE/MLE is a plausible hiring class; it is not a claim that every currently-open role
is entry level.

The exact linked URL in each row is the primary live source and is also the evidence
for the stated count. Counts are volatile; re-run the request before changing
`sources.json` later.

## A. Supported now — Greenhouse (73)

All rows use the current fetcher’s exact endpoint:
`https://boards-api.greenhouse.io/v1/boards/<slug>/jobs`.

| Employer | Focus | Exact board / live verification |
|---|---|---|
| Anthropic | AI lab | [`anthropic` — 400 jobs](https://boards-api.greenhouse.io/v1/boards/anthropic/jobs) |
| Databricks | data/AI | [`databricks` — 804 jobs](https://boards-api.greenhouse.io/v1/boards/databricks/jobs) |
| Stripe | fintech | [`stripe` — 540 jobs](https://boards-api.greenhouse.io/v1/boards/stripe/jobs) |
| Figma | product/design | [`figma` — 179 jobs](https://boards-api.greenhouse.io/v1/boards/figma/jobs) |
| Scale AI | AI data | [`scaleai` — 209 jobs](https://boards-api.greenhouse.io/v1/boards/scaleai/jobs) |
| Airtable | product/data | [`airtable` — 41 jobs](https://boards-api.greenhouse.io/v1/boards/airtable/jobs) |
| Vercel | developer infrastructure | [`vercel` — 78 jobs](https://boards-api.greenhouse.io/v1/boards/vercel/jobs) |
| Attentive | marketing infrastructure | [`attentive` — 44 jobs](https://boards-api.greenhouse.io/v1/boards/attentive/jobs) |
| Robinhood | fintech | [`robinhood` — 129 jobs](https://boards-api.greenhouse.io/v1/boards/robinhood/jobs) |
| Gusto | fintech | [`gusto` — 83 jobs](https://boards-api.greenhouse.io/v1/boards/gusto/jobs) |
| Brex | fintech | [`brex` — 288 jobs](https://boards-api.greenhouse.io/v1/boards/brex/jobs) |
| Cloudflare | internet infrastructure | [`cloudflare` — 283 jobs](https://boards-api.greenhouse.io/v1/boards/cloudflare/jobs) |
| Asana | collaboration software | [`asana` — 144 jobs](https://boards-api.greenhouse.io/v1/boards/asana/jobs) |
| Lyft | mobility | [`lyft` — 162 jobs](https://boards-api.greenhouse.io/v1/boards/lyft/jobs) |
| Reddit | consumer platform | [`reddit` — 193 jobs](https://boards-api.greenhouse.io/v1/boards/reddit/jobs) |
| Nuro | autonomy | [`nuro` — 98 jobs](https://boards-api.greenhouse.io/v1/boards/nuro/jobs) |
| Datadog | observability | [`datadog` — 424 jobs](https://boards-api.greenhouse.io/v1/boards/datadog/jobs) |
| Twilio | communications infrastructure | [`twilio` — 184 jobs](https://boards-api.greenhouse.io/v1/boards/twilio/jobs) |
| MongoDB | data infrastructure | [`mongodb` — 393 jobs](https://boards-api.greenhouse.io/v1/boards/mongodb/jobs) |
| Samsara | IoT/physical operations | [`samsara` — 309 jobs](https://boards-api.greenhouse.io/v1/boards/samsara/jobs) |
| Pinterest | consumer platform | [`pinterest` — 211 jobs](https://boards-api.greenhouse.io/v1/boards/pinterest/jobs) |
| GitLab | developer platform | [`gitlab` — 185 jobs](https://boards-api.greenhouse.io/v1/boards/gitlab/jobs) |
| Flexport | logistics technology | [`flexport` — 151 jobs](https://boards-api.greenhouse.io/v1/boards/flexport/jobs) |
| Affirm | fintech | [`affirm` — 181 jobs](https://boards-api.greenhouse.io/v1/boards/affirm/jobs) |
| Algolia | search infrastructure | [`algolia` — 41 jobs](https://boards-api.greenhouse.io/v1/boards/algolia/jobs) |
| Amplitude | product analytics | [`amplitude` — 43 jobs](https://boards-api.greenhouse.io/v1/boards/amplitude/jobs) |
| Braze | customer-engagement infrastructure | [`braze` — 229 jobs](https://boards-api.greenhouse.io/v1/boards/braze/jobs) |
| Checkr | identity/fintech infrastructure | [`checkr` — 54 jobs](https://boards-api.greenhouse.io/v1/boards/checkr/jobs) |
| CircleCI | developer infrastructure | [`circleci` — 7 jobs](https://boards-api.greenhouse.io/v1/boards/circleci/jobs) |
| Cockroach Labs | database infrastructure | [`cockroachlabs` — 31 jobs](https://boards-api.greenhouse.io/v1/boards/cockroachlabs/jobs) |
| Contentful | content infrastructure | [`contentful` — 27 jobs](https://boards-api.greenhouse.io/v1/boards/contentful/jobs) |
| Coursera | education technology | [`coursera` — 18 jobs](https://boards-api.greenhouse.io/v1/boards/coursera/jobs) |
| Cribl | observability | [`cribl` — 69 jobs](https://boards-api.greenhouse.io/v1/boards/cribl/jobs) |
| Elastic | search/data infrastructure | [`elastic` — 224 jobs](https://boards-api.greenhouse.io/v1/boards/elastic/jobs) |
| Epic Games | developer/consumer platform | [`epicgames` — 139 jobs](https://boards-api.greenhouse.io/v1/boards/epicgames/jobs) |
| Fivetran | data infrastructure | [`fivetran` — 202 jobs](https://boards-api.greenhouse.io/v1/boards/fivetran/jobs) |
| GoFundMe | consumer fintech | [`gofundme` — 36 jobs](https://boards-api.greenhouse.io/v1/boards/gofundme/jobs) |
| Hightouch | data infrastructure | [`hightouch` — 67 jobs](https://boards-api.greenhouse.io/v1/boards/hightouch/jobs) |
| Instabase | AI/document infrastructure | [`instabase` — 5 jobs](https://boards-api.greenhouse.io/v1/boards/instabase/jobs) |
| Intercom | customer software | [`intercom` — 131 jobs](https://boards-api.greenhouse.io/v1/boards/intercom/jobs) |
| Klaviyo | marketing technology | [`klaviyo` — 147 jobs](https://boards-api.greenhouse.io/v1/boards/klaviyo/jobs) |
| LaunchDarkly | developer infrastructure | [`launchdarkly` — 34 jobs](https://boards-api.greenhouse.io/v1/boards/launchdarkly/jobs) |
| Bitwarden | security infrastructure | [`bitwarden` — 10 jobs](https://boards-api.greenhouse.io/v1/boards/bitwarden/jobs) |
| Blend | fintech | [`blend` — 8 jobs](https://boards-api.greenhouse.io/v1/boards/blend/jobs) |
| Carta | fintech | [`carta` — 59 jobs](https://boards-api.greenhouse.io/v1/boards/carta/jobs) |
| Celonis | process/data software | [`celonis` — 243 jobs](https://boards-api.greenhouse.io/v1/boards/celonis/jobs) |
| Chime | fintech | [`chime` — 67 jobs](https://boards-api.greenhouse.io/v1/boards/chime/jobs) |
| EarnIn | fintech | [`earnin` — 32 jobs](https://boards-api.greenhouse.io/v1/boards/earnin/jobs) |
| Fastly | internet infrastructure | [`fastly` — 54 jobs](https://boards-api.greenhouse.io/v1/boards/fastly/jobs) |
| Lattice | people software | [`lattice` — 4 jobs](https://boards-api.greenhouse.io/v1/boards/lattice/jobs) |
| Mixpanel | product analytics | [`mixpanel` — 44 jobs](https://boards-api.greenhouse.io/v1/boards/mixpanel/jobs) |
| OpenTable | marketplace/platform | [`opentable` — 59 jobs](https://boards-api.greenhouse.io/v1/boards/opentable/jobs) |
| PagerDuty | operations infrastructure | [`pagerduty` — 20 jobs](https://boards-api.greenhouse.io/v1/boards/pagerduty/jobs) |
| Postscript | commerce infrastructure | [`postscript` — 5 jobs](https://boards-api.greenhouse.io/v1/boards/postscript/jobs) |
| Qualtrics | experience/data software | [`qualtrics` — 52 jobs](https://boards-api.greenhouse.io/v1/boards/qualtrics/jobs) |
| Rubrik | data security | [`rubrik` — 107 jobs](https://boards-api.greenhouse.io/v1/boards/rubrik/jobs) |
| Sisense | analytics software | [`sisense` — 5 jobs](https://boards-api.greenhouse.io/v1/boards/sisense/jobs) |
| Smartsheet | collaboration software | [`smartsheet` — 93 jobs](https://boards-api.greenhouse.io/v1/boards/smartsheet/jobs) |
| SoFi | fintech | [`sofi` — 62 jobs](https://boards-api.greenhouse.io/v1/boards/sofi/jobs) |
| Toast | fintech/commerce | [`toast` — 280 jobs](https://boards-api.greenhouse.io/v1/boards/toast/jobs) |
| Workato | automation infrastructure | [`workato` — 155 jobs](https://boards-api.greenhouse.io/v1/boards/workato/jobs) |
| ZipRecruiter | hiring platform | [`ziprecruiter` — 36 jobs](https://boards-api.greenhouse.io/v1/boards/ziprecruiter/jobs) |
| Duolingo | consumer/education technology | [`duolingo` — 67 jobs](https://boards-api.greenhouse.io/v1/boards/duolingo/jobs) |
| Fireblocks | crypto/fintech infrastructure | [`fireblocks` — 66 jobs](https://boards-api.greenhouse.io/v1/boards/fireblocks/jobs) |
| Human Interest | fintech | [`humaninterest` — 67 jobs](https://boards-api.greenhouse.io/v1/boards/humaninterest/jobs) |
| Khan Academy | education technology | [`khanacademy` — 24 jobs](https://boards-api.greenhouse.io/v1/boards/khanacademy/jobs) |
| New Relic | observability | [`newrelic` — 56 jobs](https://boards-api.greenhouse.io/v1/boards/newrelic/jobs) |
| Sendbird | communications infrastructure | [`sendbird` — 18 jobs](https://boards-api.greenhouse.io/v1/boards/sendbird/jobs) |
| SmartAsset | fintech | [`smartasset` — 5 jobs](https://boards-api.greenhouse.io/v1/boards/smartasset/jobs) |
| Udemy | education technology | [`udemy` — 12 jobs](https://boards-api.greenhouse.io/v1/boards/udemy/jobs) |
| Upwork | marketplace/platform | [`upwork` — 11 jobs](https://boards-api.greenhouse.io/v1/boards/upwork/jobs) |
| Yext | search/data software | [`yext` — 26 jobs](https://boards-api.greenhouse.io/v1/boards/yext/jobs) |
| Zscaler | security infrastructure | [`zscaler` — 310 jobs](https://boards-api.greenhouse.io/v1/boards/zscaler/jobs) |

## B. Supported now — Lever (1)

| Employer | Focus | Exact board / live verification |
|---|---|---|
| Palantir | data/AI platform | [`palantir` — 284 jobs](https://api.lever.co/v0/postings/palantir?mode=json) |

The current fetcher calls exactly `https://api.lever.co/v0/postings/<slug>?mode=json`.
The many 404s encountered for plausible names are why no speculative Lever identifier
is included.

## C. Supported now — Ashby (31)

All rows use the current fetcher’s exact endpoint:
`https://api.ashbyhq.com/posting-api/job-board/<slug>`.

| Employer | Focus | Exact board / live verification |
|---|---|---|
| Notion | collaboration software | [`notion` — 113 listed jobs](https://api.ashbyhq.com/posting-api/job-board/notion) |
| Benchling | life-science software | [`benchling` — 51 listed jobs](https://api.ashbyhq.com/posting-api/job-board/benchling) |
| Ramp | fintech | [`ramp` — 125 listed jobs](https://api.ashbyhq.com/posting-api/job-board/ramp) |
| Plaid | fintech infrastructure | [`plaid` — 116 listed jobs](https://api.ashbyhq.com/posting-api/job-board/plaid) |
| Linear | developer/product software | [`linear` — 23 listed jobs](https://api.ashbyhq.com/posting-api/job-board/linear) |
| Vanta | security/compliance infrastructure | [`vanta` — 101 listed jobs](https://api.ashbyhq.com/posting-api/job-board/vanta) |
| PostHog | product/data infrastructure | [`posthog` — 9 listed jobs](https://api.ashbyhq.com/posting-api/job-board/posthog) |
| Modern Treasury | fintech infrastructure | [`moderntreasury` — 8 listed jobs](https://api.ashbyhq.com/posting-api/job-board/moderntreasury) |
| Anyscale | AI infrastructure | [`anyscale` — 21 listed jobs](https://api.ashbyhq.com/posting-api/job-board/anyscale) |
| Perplexity | AI lab/product | [`perplexity` — 87 listed jobs](https://api.ashbyhq.com/posting-api/job-board/perplexity) |
| Runway | AI media | [`runway` — 4 listed jobs](https://api.ashbyhq.com/posting-api/job-board/runway) |
| Harvey | legal AI | [`harvey` — 349 listed jobs](https://api.ashbyhq.com/posting-api/job-board/harvey) |
| Decagon | AI agents | [`decagon` — 115 listed jobs](https://api.ashbyhq.com/posting-api/job-board/decagon) |
| Cognition | AI lab | [`cognition` — 79 listed jobs](https://api.ashbyhq.com/posting-api/job-board/cognition) |
| Sierra | AI agents | [`sierra` — 172 listed jobs](https://api.ashbyhq.com/posting-api/job-board/sierra) |
| Cursor | AI developer tools | [`cursor` — 119 listed jobs](https://api.ashbyhq.com/posting-api/job-board/cursor) |
| Baseten | AI infrastructure | [`baseten` — 62 listed jobs](https://api.ashbyhq.com/posting-api/job-board/baseten) |
| Modal | AI/cloud infrastructure | [`modal` — 34 listed jobs](https://api.ashbyhq.com/posting-api/job-board/modal) |
| Pinecone | AI/vector-data infrastructure | [`pinecone` — 6 listed jobs](https://api.ashbyhq.com/posting-api/job-board/pinecone) |
| LangChain | AI developer infrastructure | [`langchain` — 91 listed jobs](https://api.ashbyhq.com/posting-api/job-board/langchain) |
| LlamaIndex | AI developer infrastructure | [`llamaindex` — 14 listed jobs](https://api.ashbyhq.com/posting-api/job-board/llamaindex) |
| Supabase | developer/data infrastructure | [`supabase` — 55 listed jobs](https://api.ashbyhq.com/posting-api/job-board/supabase) |
| Neon | database infrastructure | [`neon` — 7 listed jobs](https://api.ashbyhq.com/posting-api/job-board/neon) |
| Materialize | streaming-data infrastructure | [`materialize` — 5 listed jobs](https://api.ashbyhq.com/posting-api/job-board/materialize) |
| MotherDuck | data infrastructure | [`motherduck` — 5 listed jobs](https://api.ashbyhq.com/posting-api/job-board/motherduck) |
| Semgrep | developer/security infrastructure | [`semgrep` — 17 listed jobs](https://api.ashbyhq.com/posting-api/job-board/semgrep) |
| Crusoe | AI/cloud infrastructure | [`crusoe` — 363 listed jobs](https://api.ashbyhq.com/posting-api/job-board/crusoe) |
| Skydio | autonomy/robotics | [`skydio` — 112 listed jobs](https://api.ashbyhq.com/posting-api/job-board/skydio) |
| Pylon | developer/customer infrastructure | [`pylon` — 12 listed jobs](https://api.ashbyhq.com/posting-api/job-board/pylon) |
| Orb | billing infrastructure | [`orb` — 26 listed jobs](https://api.ashbyhq.com/posting-api/job-board/orb) |
| OpenAI | AI lab | [`openai` — 750 listed jobs](https://api.ashbyhq.com/posting-api/job-board/openai) |

## D. Live direct boards, but not consumable by current code (2)

These are deliberately **not** in the JSON proposal. They are verified as live career
search endpoints with current role/search content, but neither exposes a Greenhouse,
Lever, or Ashby endpoint that `job_alert.py` can read. The identifier is the explicit
direct-board path/query, not an invented slug.

| Employer | ATS / identifier | Official live endpoint and verification | Needed support |
|---|---|---|---|
| Meta | Meta Careers direct board; `/jobs/` | [Meta Careers jobs](https://www.metacareers.com/jobs/) returned a live HTML job board containing `Software engineer` role/search content on 2026-07-30. | A Meta Careers fetcher or an authenticated/undocumented-data policy decision. |
| Cisco | Cisco Careers direct board; `SearchJobs/?21178=[169]&21178_format=6020&listFilterMode=1` | [Cisco machine-learning search](https://jobs.cisco.com/jobs/SearchJobs/?21178=%5B169%5D&21178_format=6020&listFilterMode=1) returned a live HTML board containing `Machine Learning` content on 2026-07-30. | A Cisco Careers fetcher; do not put this URL in `sources.json`. |

Important exclusions: direct probes of Apple’s search API returned `401`, while some
other major-company pages served a client-side search shell rather than verifiable
result records. They are not entered as candidates because a merely reachable careers
page does not satisfy this ticket’s non-empty-job requirement.

## Concrete `sources.json` proposal (supported entries only)

This preserves the exact existing schema and contains only the 105 endpoint-verified
identifiers that the present `fetch_greenhouse`, `fetch_lever`, and `fetch_ashby`
functions can read. It is a research payload, **not an edit to `sources.json`**.

```json
{
  "greenhouse": [
    "anthropic", "databricks", "stripe", "figma", "scaleai", "airtable", "vercel", "attentive",
    "robinhood", "gusto", "brex", "cloudflare", "asana", "lyft", "reddit", "nuro", "datadog",
    "twilio", "mongodb", "samsara", "pinterest", "gitlab", "flexport", "affirm", "algolia",
    "amplitude", "braze", "checkr", "circleci", "cockroachlabs", "contentful", "coursera", "cribl",
    "elastic", "epicgames", "fivetran", "gofundme", "hightouch", "instabase", "intercom", "klaviyo",
    "launchdarkly", "bitwarden", "blend", "carta", "celonis", "chime", "earnin", "fastly", "lattice",
    "mixpanel", "opentable", "pagerduty", "postscript", "qualtrics", "rubrik", "sisense", "smartsheet",
    "sofi", "toast", "workato", "ziprecruiter", "duolingo", "fireblocks", "humaninterest", "khanacademy",
    "newrelic", "sendbird", "smartasset", "udemy", "upwork", "yext", "zscaler"
  ],
  "lever": ["palantir"],
  "ashby": [
    "notion", "benchling", "ramp", "plaid", "linear", "vanta", "posthog", "moderntreasury",
    "anyscale", "perplexity", "runway", "harvey", "decagon", "cognition", "sierra", "cursor",
    "baseten", "modal", "pinecone", "langchain", "llamaindex", "supabase", "neon", "materialize",
    "motherduck", "semgrep", "crusoe", "skydio", "pylon", "orb", "openai"
  ]
}
```

The payload adds **65 Greenhouse**, **1 Lever**, and **27 Ashby** sources to the
current 12-source file (the original eight Greenhouse and four Ashby boards were also
live and are retained), for **93 net additions**. The runtime decision permits enabling
all 105 with bounded parallel fetching.

## Marginal value versus Simplify, and limitations

The configured Simplify primary feed was live on the same date and contained **17,741**
rows. It is an intentionally broad new-grad feed, so there is necessarily cross-post
overlap — especially for large Greenhouse employers such as Stripe, Databricks,
Cloudflare, and Figma. No company-level overlap percentage is claimed here: measuring
it correctly requires joining live Simplify rows with board records using ticket 09’s
Cross-post rule, not comparing company names.

High marginal-value additions are the boards most likely to protect against aggregator
lag, omission, or broad-feed filtering: AI labs and AI infrastructure (OpenAI,
Anthropic, Perplexity, Cursor, Anyscale, Baseten, Modal, LangChain, LlamaIndex,
Decagon, Cognition, Sierra, Harvey, Scale AI); smaller infrastructure companies
(Pylon, Orb, MotherDuck, Materialize, Neon, Semgrep, Hightouch, Cribl, LaunchDarkly,
Workato); and fintechs with their own board coverage (Brex, Chime, Carta, EarnIn,
Modern Treasury, Human Interest, Fireblocks). Direct-first collection also
captures records whose title does not meet Simplify’s inclusion rules, preserving the
project’s recall-first store.

Likely high-redundancy additions are the already-prominent public employers in the
Simplify feed: Stripe, Databricks, Figma, Robinhood, Cloudflare, Lyft, Pinterest,
Twilio, MongoDB, Reddit, and the larger public SaaS set. They remain useful as a
source-of-record and anti-lag backstop, but should be prioritised after the high-value
set if the sequential source budget is tight.

Uncertainties to carry forward:

- Board slugs and counts can change without warning; re-verify a zero-result board
  before treating it as a company hiring pause.
- The `lendingclub` Greenhouse board verified with 14 jobs during the initial survey,
  then returned HTTP 404 during the same-day 106-board runtime benchmark. It was
  removed from the proposal immediately; re-add LendingClub only after locating and
  verifying its current first-party board.
- This is endpoint verification, not a guarantee of a currently-open Bay Area or
  entry-level SWE/MLE Record. The current filters and score semantics in `CONTEXT.md`
  make that decision at scan/query time.
- Several companies in the inventory have multi-city or remote hiring footprints. The
  company-selection judgment is necessarily less exact than the endpoint evidence;
  only the latter is asserted as live fact.
- Direct-board giants were intentionally omitted when their public page did not expose
  verifiable current records. Adding a fetcher for a vendor is preferable to guessing a
  slug or scraping an unstable shell.
