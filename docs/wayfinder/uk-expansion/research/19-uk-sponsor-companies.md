# UK sponsor-company list and verified board slugs

**Research date:** 2026-08-01
**Ticket:** [Assemble the UK sponsor-company list and verify board slugs](../tickets/19-uk-sponsor-company-list.md)
**Precedent followed:** [Target company list and verified board identifiers](../../research/06-target-company-list.md)
**Adapter boundary:** [ATS Platform Public API Survey](../../research/05-ats-platform-survey.md)

## Bottom line

**Add 45 net-new board slugs.** Every one was fetched read-only on 2026-08-01 and observed
to return JSON containing **at least one UK posting**. Nothing here is a guessed slug, and
nothing here duplicates `sources.json` (checked programmatically against all 109 entries —
zero collisions).

By adapter: **greenhouse 15**, **lever 3**, **ashby 24**, **smartrecruiters 1**,
**workable 2**, **recruitee 0**. That takes the Source Inventory from **109 → 154**
entries, the number [the scan-time budget ticket](../tickets/21-scan-time-budget.md) needs.

Two headline results worth acting on before the rest:

- **Graphcore (`graphcore`, greenhouse) is the single best UK source found.** 225 postings,
  **111 UK**, 94 of them engineering titles, and it is carrying
  `2026 Graduate Firmware Engineer` and `2026 Graduate Silicon Engineer` — Score Band **15**
  under the *current* classifier, no UK vocabulary change required.
- **Eight of the 45 boards already carry a Score ≥5 UK entry-level engineering title today**
  (see [Score evidence](#score-evidence-the-list-pays-off-under-the-current-classifier)).
  This list is not speculative coverage; it produces Candidates immediately.

If the scan-time budget forces a phased rollout, add the **31 Tier A** boards first and
defer the **14 Tier B** boards — the split is defined and listed
[below](#tier-a-vs-tier-b-if-the-scan-time-budget-bites).

**No recommended company numbers its new-grad rung as L4+/E4+.** The `L4+/E4+` hard reject
is safe against this list. A *different* leveling hazard did surface (Canonical, Wise, Tide)
— see [Leveling conventions](#leveling-conventions-what-to-flag-for-ticket-17).

## Method, and what "verified" means here

This ticket's bar is **stricter than ticket 06's**. Ticket 06 accepted "the board is
reachable and non-empty". Here a row must clear **both**:

1. the exact endpoint the current fetcher calls returned `200` JSON in the expected
   top-level shape, **and**
2. **at least one posting in that response had a UK location.**

`≥1 UK posting` is the floor, and it is deliberately a floor, not "a UK-heavy board". A
board with 400 postings and zero UK rows fails — that is what eliminated Google DeepMind,
Mollie, and Stability AI below. Counts are volatile; re-verify before
`sources.json` is edited.

The probe called only the six supported adapters at their exact configured endpoints
(`fetch_greenhouse` / `fetch_lever` / `fetch_ashby` / `fetch_smartrecruiters` /
`fetch_workable` / `fetch_recruitee` in `job_alert.py`), unauthenticated, sequential, with a
plain User-Agent and a 0.35 s inter-request sleep. No authentication, no rate-limit evasion,
no bot-protection bypass. Where a careers page refused an ordinary read (Revolut, HTTP 403)
it was recorded as not publicly fetchable and abandoned.

### UK location matching

Locations were evaluated **segment-wise**, splitting multi-location strings on `;` / `|`,
because the map already recorded live US/UK city-name collisions. A segment counts as UK on
an explicit marker (`United Kingdom`, `UK`, `England`, `Scotland`, `Wales`,
`Northern Ireland`, `GB`) or on a bare UK city with no competing US-state / US / other-country
marker in that same segment.

This matters — the naive version was wrong. A whole-string matcher scored
`Kirkland, Washington, US; Mountain View, California, US; New York City, New York, US` as UK,
because **"New York City" contains "York"**. Segment-wise evaluation both kills that false
positive and keeps the true positive `London, UK; New York, US`. `Cambridge, MA`,
`Birmingham, AL`, and `Brighton, CO - US` are all correctly rejected.

### Evidence labels

- **Documented** — a published source says it. Here: a row in the Home Office register, or
  vendor documentation.
- **Observed 2026-08-01** — a read-only request returned this result on that date. Every
  slug, posting count, UK count, and title in this file is Observed. A live result is not a
  promise about a future request.
- **Inference** — my judgment, marked as such. Never dressed as documentation.

### The sponsor signal: the Home Office register

**Documented.** The Home Office publishes the
[Register of licensed sponsors: workers](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers)
as a single **CSV**, currently
[`SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-07-31.csv`](https://assets.publishing.service.gov.uk/media/6a6c58e60ddb7e4831c62aa3/SP_-_Worker_and_Temporary_Worker_Web_Register_-_2026-07-31.csv)
(10.4 MB, page states last updated **31 July 2026**). **Observed 2026-08-01:** retrieved
`200`, 10,915,962 bytes, **142,649 rows**, columns
`Organisation Name, Town/City, County, Type & Rating, Route`.

So: **yes, it is retrievable as a stable machine-readable file.** It is used here exactly as
the charted decision intends — a **human curation reference**, not a runtime join. No
automated name matcher was built and none should be. The dated filename means the URL is not
a permanent link; the landing page is the stable entry point.

Three limits on this evidence, stated once and applying to every **Documented** row:

1. **A register row proves the entity holds a sponsor licence. It does not prove the company
   sponsors new grads**, or that any specific posting is open to sponsorship. That gap is
   irreducible from the register alone.
2. **The brand→legal-entity link is a human match I performed.** I label it **Documented**
   only where the registered name unambiguously contains the brand *and* the town matches
   the company's known UK base (`Monzo` → `Monzo Bank Ltd, London`;
   `Deliveroo` → `Roofoods Ltd t/a Deliveroo, London`). Where the link needed a guess about
   the legal entity, the row is **Inference** and names the candidate entity.
3. Name normalisation is genuinely awkward (`ElevenLabs` is registered as `Eleven Labs Ltd`;
   `Faculty` as `Faculty Science Limited`). Per the ticket this is explicitly **not** a
   blocker, and it did not block anything.

## Recommended net-new slugs (45)

"UK eng-role titles" counts UK postings whose title passes the current `ROLE_MATCH` — a
relevance signal, not a claim any of them is entry-level.

| Company | ATS | Verified slug | Observed | Postings (total / UK) | UK eng-role titles | Sponsor evidence (Home Office register of licensed sponsors, 2026-07-31 file) | Label | Status |
|---|---|---|---:|---:|---:|---|---|---|
| Graphcore | greenhouse | [`graphcore`](https://boards-api.greenhouse.io/v1/boards/graphcore/jobs) | 2026-08-01 | 225 / **111** | 94 | Graphcore Limited, Bristol — Skilled Worker | **Documented** | net-new |
| SumUp | greenhouse | [`sumup`](https://boards-api.greenhouse.io/v1/boards/sumup/jobs) | 2026-08-01 | 372 / **76** | 3 | SumUp Payments Limited, London — Skilled Worker | **Documented** | net-new |
| Monzo | greenhouse | [`monzo`](https://boards-api.greenhouse.io/v1/boards/monzo/jobs) | 2026-08-01 | 72 / **54** | 17 | Monzo Bank Ltd, London — Skilled Worker | **Documented** | net-new |
| Man Group | greenhouse | [`mangroup`](https://boards-api.greenhouse.io/v1/boards/mangroup/jobs) | 2026-08-01 | 58 / **22** | 5 | no register row found under Man Group / Man Investments / AHL | **Inference** | net-new |
| Isomorphic Labs | greenhouse | [`isomorphiclabs`](https://boards-api.greenhouse.io/v1/boards/isomorphiclabs/jobs) | 2026-08-01 | 23 / **18** | 9 | Isomorphic Labs Limited, London — Skilled Worker | **Documented** | net-new |
| Tide | greenhouse | [`tide`](https://boards-api.greenhouse.io/v1/boards/tide/jobs) | 2026-08-01 | 105 / **17** | 4 | Tide Platform Ltd, London — Skilled Worker | **Documented** | net-new |
| PhysicsX | greenhouse | [`physicsx`](https://boards-api.greenhouse.io/v1/boards/physicsx/jobs) | 2026-08-01 | 41 / **15** | 8 | PhysicsX Limited, London — Skilled Worker | **Documented** | net-new |
| Grafana Labs | greenhouse | [`grafanalabs`](https://boards-api.greenhouse.io/v1/boards/grafanalabs/jobs) | 2026-08-01 | 142 / **15** | 14 | Grafana Labs Ltd, London — Skilled Worker | **Documented** | net-new |
| GoCardless | greenhouse | [`gocardless`](https://boards-api.greenhouse.io/v1/boards/gocardless/jobs) | 2026-08-01 | 30 / **13** | 3 | GoCardless Limited, London — Skilled Worker | **Documented** | net-new |
| ComplyAdvantage | greenhouse | [`complyadvantage`](https://boards-api.greenhouse.io/v1/boards/complyadvantage/jobs) | 2026-08-01 | 29 / **11** | 3 | no row under "ComplyAdvantage"; `IVXS UK Limited, London` is the likely legal entity | **Inference** | net-new |
| Canonical | greenhouse | [`canonical`](https://boards-api.greenhouse.io/v1/boards/canonical/jobs) | 2026-08-01 | 303 / **11** | 2 | Canonical UK Limited, London — Skilled Worker | **Documented** | net-new |
| IMC Trading | greenhouse | [`imc`](https://boards-api.greenhouse.io/v1/boards/imc/jobs) | 2026-08-01 | 159 / **11** | 5 | no register row found under IMC / IMC Trading / IMC Financial ([tenant identity confirmed separately](#the-three-letter-imc-slug-tenant-identity-confirmed)) | **Inference** | net-new |
| Squarepoint Capital | greenhouse | [`squarepointcapital`](https://boards-api.greenhouse.io/v1/boards/squarepointcapital/jobs) | 2026-08-01 | 88 / **8** | 4 | Squarepoint Capital LLP, London — Skilled Worker | **Documented** | net-new |
| Typeform | greenhouse | [`typeform`](https://boards-api.greenhouse.io/v1/boards/typeform/jobs) | 2026-08-01 | 12 / **7** | 0 | Typeform UK Limited, London — Skilled Worker | **Documented** | net-new |
| PolyAI | greenhouse | [`polyai`](https://boards-api.greenhouse.io/v1/boards/polyai/jobs) | 2026-08-01 | 15 / **3** | 1 | PolyAI Limited, London — Skilled Worker | **Documented** | net-new |
| Octopus Energy | lever | [`octoenergy`](https://api.lever.co/v0/postings/octoenergy?mode=json) | 2026-08-01 | 143 / **61** | 11 | Octopus Energy Limited, London — Skilled Worker | **Documented** | net-new |
| Zopa | lever | [`zopa`](https://api.lever.co/v0/postings/zopa?mode=json) | 2026-08-01 | 30 / **30** | 10 | Zopa Bank Limited, London — Skilled Worker | **Documented** | net-new |
| Sonar | lever | [`sonarsource`](https://api.lever.co/v0/postings/sonarsource?mode=json) | 2026-08-01 | 117 / **14** | 4 | SonarSource UK LTD, London — Skilled Worker | **Documented** | net-new |
| Deliveroo | ashby | [`deliveroo`](https://api.ashbyhq.com/posting-api/job-board/deliveroo) | 2026-08-01 | 185 / **120** | 30 | Roofoods Ltd t/a Deliveroo, London — Skilled Worker | **Documented** | net-new |
| Faculty | ashby | [`faculty`](https://api.ashbyhq.com/posting-api/job-board/faculty) | 2026-08-01 | 67 / **67** | 44 | Faculty Science Limited, London — Skilled Worker | **Documented** | net-new |
| ElevenLabs | ashby | [`elevenlabs`](https://api.ashbyhq.com/posting-api/job-board/elevenlabs) | 2026-08-01 | 224 / **66** | 16 | Eleven Labs Ltd, London — Skilled Worker | **Documented** | net-new |
| Lendable | ashby | [`lendable`](https://api.ashbyhq.com/posting-api/job-board/lendable) | 2026-08-01 | 61 / **48** | 10 | Lendable Operations Ltd, London — Skilled Worker | **Documented** | net-new |
| Trainline | ashby | [`trainline`](https://api.ashbyhq.com/posting-api/job-board/trainline) | 2026-08-01 | 47 / **46** | 22 | Trainline.com Ltd, London — Skilled Worker | **Documented** | net-new |
| Cohere | ashby | [`cohere`](https://api.ashbyhq.com/posting-api/job-board/cohere) | 2026-08-01 | 142 / **42** | 17 | Cohere UK Ltd, London — Skilled Worker | **Documented** | net-new |
| Wayve | ashby | [`wayve`](https://api.ashbyhq.com/posting-api/job-board/wayve) | 2026-08-01 | 107 / **30** | 15 | Wayve Technologies Ltd, London — Skilled Worker | **Documented** | net-new |
| Synthesia | ashby | [`synthesia`](https://api.ashbyhq.com/posting-api/job-board/synthesia) | 2026-08-01 | 76 / **28** | 6 | Synthesia Limited, London — Skilled Worker | **Documented** | net-new |
| Multiverse | ashby | [`multiverse`](https://api.ashbyhq.com/posting-api/job-board/multiverse) | 2026-08-01 | 25 / **25** | 8 | Multiverse Group Limited, London — Skilled Worker | **Documented** | net-new |
| Pleo | ashby | [`pleo`](https://api.ashbyhq.com/posting-api/job-board/pleo) | 2026-08-01 | 42 / **21** | 11 | Pleo Technologies Limited, London — Skilled Worker | **Documented** | net-new |
| Motorway | ashby | [`motorway`](https://api.ashbyhq.com/posting-api/job-board/motorway) | 2026-08-01 | 18 / **18** | 6 | Motorway Online Limited, London — Skilled Worker | **Documented** | net-new |
| Paddle | ashby | [`paddle`](https://api.ashbyhq.com/posting-api/job-board/paddle) | 2026-08-01 | 20 / **17** | 6 | Paddle.com Market Limited, London — Skilled Worker | **Documented** | net-new |
| Marshmallow | ashby | [`marshmallow`](https://api.ashbyhq.com/posting-api/job-board/marshmallow) | 2026-08-01 | 16 / **16** | 5 | Marshmallow Technology Ltd, London — Skilled Worker | **Documented** | net-new |
| Zilch | ashby | [`zilch`](https://api.ashbyhq.com/posting-api/job-board/zilch) | 2026-08-01 | 14 / **13** | 4 | Zilch Technology Limited, London — Skilled Worker | **Documented** | net-new |
| OakNorth | ashby | [`oaknorth`](https://api.ashbyhq.com/posting-api/job-board/oaknorth) | 2026-08-01 | 27 / **13** | 0 | OakNorth Bank Plc, London — Skilled Worker | **Documented** | net-new |
| Quantexa | ashby | [`quantexa`](https://api.ashbyhq.com/posting-api/job-board/quantexa) | 2026-08-01 | 32 / **9** | 7 | Quantexa Ltd, London — Skilled Worker | **Documented** | net-new |
| Freetrade | ashby | [`freetrade`](https://api.ashbyhq.com/posting-api/job-board/freetrade) | 2026-08-01 | 7 / **7** | 5 | Freetrade Limited, London — Skilled Worker | **Documented** | net-new |
| Beamery | ashby | [`beamery`](https://api.ashbyhq.com/posting-api/job-board/beamery) | 2026-08-01 | 7 / **6** | 3 | Beamery Ltd, London — Skilled Worker | **Documented** | net-new |
| Skyscanner | ashby | [`skyscanner`](https://api.ashbyhq.com/posting-api/job-board/skyscanner) | 2026-08-01 | 7 / **5** | 2 | Skyscanner Limited, Edinburgh — Skilled Worker | **Documented** | net-new |
| Smarkets | ashby | [`smarkets`](https://api.ashbyhq.com/posting-api/job-board/smarkets) | 2026-08-01 | 10 / **5** | 3 | Smarkets Limited, London — Skilled Worker | **Documented** | net-new |
| Improbable | ashby | [`improbable`](https://api.ashbyhq.com/posting-api/job-board/improbable) | 2026-08-01 | 9 / **4** | 1 | Improbable Worlds Ltd, London — Skilled Worker | **Documented** | net-new |
| Griffin | ashby | [`griffin`](https://api.ashbyhq.com/posting-api/job-board/griffin) | 2026-08-01 | 3 / **3** | 1 | Griffin Bank Ltd, London — Skilled Worker | **Documented** | net-new |
| Miro | ashby | [`miro`](https://api.ashbyhq.com/posting-api/job-board/miro) | 2026-08-01 | 44 / **3** | 0 | Miro EMEA UK Ltd., London — Skilled Worker | **Documented** | net-new |
| Zego | ashby | [`zego`](https://api.ashbyhq.com/posting-api/job-board/zego) | 2026-08-01 | 2 / **1** | 1 | no row under "Zego"; `EXTRACOVER LIMITED, London` is the likely legal entity | **Inference** | net-new |
| Wise | smartrecruiters | [`Wise`](https://api.smartrecruiters.com/v1/companies/Wise/postings?limit=100&offset=0) | 2026-08-01 | 406 / **148** | 62 | Wise Payments Limited, London — Skilled Worker | **Documented** | net-new |
| Plum | workable | [`withplum`](https://www.workable.com/api/accounts/withplum?details=true) | 2026-08-01 | 32 / **8** | 4 | Plum Fintech, London — Skilled Worker | **Documented** | net-new |
| Yapily | workable | [`yapily`](https://www.workable.com/api/accounts/yapily?details=true) | 2026-08-01 | 11 / **8** | 4 | Yapily Limited, London — Skilled Worker | **Documented** | net-new |

Each linked URL is the primary live source and the evidence for its own counts.

### The three-letter `imc` slug: tenant identity confirmed

`imc` is the shortest and highest-collision slug in this list, and it is also one of the
**Inference**-only sponsor rows — two weaknesses that compound, so it got the same scrutiny
that made me drop `cleo`. **Observed 2026-08-01**, the board is IMC Trading:

- Apply URLs resolve to `https://job-boards.eu.greenhouse.io/imc/...` — an **EU**
  data-residency tenant, consistent with an Amsterdam-headquartered firm.
- Office distribution across the 159 postings — Chicago 51, Amsterdam 31, Sydney 26,
  Mumbai 13, London 12 — matches IMC Trading's known office set exactly.
- Titles are market-maker specific: `Commodities Volatility Trader`,
  `Quantitative Researcher - Equities`, `Lead Alpha Researcher, Systematic Equities`,
  `Trading Strategy Software Engineer`, plus the literal string `IMC Trading` in an event
  posting.

That is conclusive on identity. It does **not** upgrade the sponsor label, which stays
**Inference**.

The two other generic-word slugs are convincing on title inspection alone and were accepted:
`faculty` (`UK Defence Veterans - Civilian Work Attachment`, locations `UK - London` /
`UK - Remote`) and `griffin` (`Fincrime Assurance Associate`, `London or remote within the UK`).

### Greenhouse EU tenants work unchanged — a partial answer to the map's fog

**Observed 2026-08-01.** The map lists *"Cross-post identity under UK/EU ATS tenants"* as
unspecified fog. Partial answer, for Greenhouse at least:

**4 of the 15 Greenhouse boards are on the EU data-residency tenant**
(`job-boards.eu.greenhouse.io`: `mangroup`, `physicsx`, `imc`, `polyai`) — and **all four
were readable through the standard `boards-api.greenhouse.io/v1/boards/{slug}/jobs`
endpoint with no change to `fetch_greenhouse`.** The EU tenant is not a transport problem.

What *does* differ is the apply-URL host, and it is not only an EU/US split. Across the 15
boards the `absolute_url` host was one of:

| Apply-URL host | Count | Boards |
|---|---:|---|
| `job-boards.greenhouse.io` | 8 | graphcore, monzo, isomorphiclabs, tide, grafanalabs, gocardless, canonical, typeform |
| `job-boards.eu.greenhouse.io` | 4 | mangroup, physicsx, imc, polyai |
| company's own domain | 3 | `sumup.com`, `complyadvantage.com`, `www.squarepoint-capital.com` |

**Inference:** three of these boards hand back apply URLs that contain **no `greenhouse.io`
host at all**. Any logic that infers platform or tenant from the apply URL — rather than from
the configured source and the platform job ID — would misread those three. Ticket 09's
Opening Identity is specified on the platform's own immutable job ID, so this should be
harmless, but it is worth confirming rather than assuming.

### Score evidence: the list pays off under the current classifier

**Observed 2026-08-01.** Running the repo's own `classify()` over the UK postings on these
boards, eight already produce a Score ≥5 title — before any of
[ticket 17](../tickets/17-classify-uk-titles.md)'s UK vocabulary work:

| Company | Band | UK title |
|---|---:|---|
| Graphcore | **15** | `2026 Graduate Firmware Engineer` (also `2026 Graduate Silicon Engineer`) |
| Deliveroo | **10** | `Software Engineer, New Grad` |
| IMC Trading | 5 | `Graduate Machine Learning Researcher - London` |
| Trainline | 5 | `Junior Engineer - .NET Backend (London)` |
| Squarepoint Capital | 5 | `Junior Software Developer - Front-end` |
| Quantexa | 5 | `Associate Data Engineer` |
| Man Group | 5 | `Associate Engineer - Finance & People Technology` |
| Cohere | 5 | `Member of Technical Staff, Modeling` (MTS rule) |

**Inference:** this understates the eventual yield. Band-3 volume is large across these
boards, and ticket 17's promotion of `Graduate <eng role>` to Band 10 will lift UK grad
schemes that currently score 3 or reject.

### Tier A vs Tier B, if the scan-time budget bites

Rule: **Tier B** = fewer than four UK engineering-role titles observed today. It is a
"defer", not a "reject" — every Tier B slug is verified.

- **Tier A (31)** — everything not listed below.
- **Tier B (14):** SumUp (3), GoCardless (3), ComplyAdvantage (3), Beamery (3),
  Smarkets (3), Canonical (2), Skyscanner (2), PolyAI (1), Improbable (1), Griffin (1),
  Zego (1), Typeform (0), OakNorth (0), Miro (0).

## Two companies live on *two* supported boards at once — pick one

**Observed 2026-08-01.** This is ticket 06's ATS-migration lesson showing up again, mid-flight:

| Company | Greenhouse | Ashby | Title overlap |
|---|---|---|---|
| Wayve | `wayve` — 109 postings / 31 UK | `wayve` — 107 postings / 30 UK | **87 of 89** unique titles identical |
| Skyscanner | `skyscanner` — 7 / 4 UK | `skyscanner` — 7 / 5 UK | **4 of 5** unique titles identical |

**Do not add both boards for either company.** The
[Opening Identity registry](../../tickets/09-dedup-across-many-sources.md) is
platform-scoped, so the same requisition arriving via Greenhouse and via Ashby would **not**
collapse — it would produce duplicate Records and duplicate notifications. This is exactly
the *"Cross-post identity under UK/EU ATS tenants"* fog the map flagged, now with a concrete
instance.

I recommend the **Ashby** slug for both: cleaner location strings
(`London, United Kingdom` vs bare `London`), one more UK posting for Skyscanner, and fewer
in-board duplicate titles. **Inference:** the pattern looks like a Greenhouse→Ashby
migration in progress, so the Greenhouse board is the one likelier to go dark. Re-check both
before editing `sources.json`; if the Ashby board has emptied, switch rather than add.

## Leveling conventions: what to flag for ticket 17

**Observed 2026-08-01 — the headline is negative, and that is good news.** I scanned every
UK title on all 45 boards for the exact patterns `HARD_NEG` rejects
(`level\s*[4-9]`, `l[4-9]\b`, `e[4-9]\b`). **Zero hits.** No recommended company numbers any
UK title L4+/E4+/Level 4+, so the `CONTEXT.md` hard reject — validated against the US list
only — is **not** silently dropping UK new-grad roles on this list. The pre-hedge the ticket
worried about is not needed.

Three companies do use non-standard numeric leveling, and all three deserve a flag for
different reasons. **Note all three tokens currently appear on non-UK postings** — these are
company-wide conventions that will reach UK titles, not live UK misclassifications:

| Company | Token observed | Where | Why it matters |
|---|---|---|---|
| Canonical | `Software Engineer - L3 Support` (`Home based - Worldwide`) | greenhouse | **False positive risk.** `WEAK_POS` matches `l3\b` → **+5 "junior-level marker"**. But Canonical's "L3" is a *third-line support tier*, not a new-grad rung. This scores a potentially senior support role as junior. |
| Wise | `IC2 Engineer` (`Austin, us`) | smartrecruiters | **Gap, not a reject.** `IC2` matches nothing — not `HARD_NEG`, not `MID_LEVEL`, not `WEAK_POS` (only `ic1\b` is junior-positive). Wise runs an IC ladder, so an `IC4 Engineer` would be **silently accepted** rather than rejected — the mirror image of the ticket's worry. |
| Tide | `Analyst, Level 1, Onboarding KYX, UK` (`India, Hyderabad`) | greenhouse | Benign today: `level\s*1\b` is junior-positive (+5) and correct, but `Analyst` fails `ROLE_MATCH` so it rejects as "not an eng/ML role" anyway. Worth knowing Tide numbers rungs as `Level N` — `Level 2` would hit `MID_LEVEL`. |

**One further UK-specific wrinkle, Observed 2026-08-01.** UK/Ireland region suffixes —
`UK/I`, `UK&I` — are common on these boards (Pleo, ElevenLabs) and put a bare Roman-numeral
`I` in the title. I checked every affected UK posting: none is currently misclassified,
because `HARD_NEG` matches `II`/`III`/`IV` but not bare `I`, and `WEAK_POS` requires the
numeral to directly follow the role noun. **Inference:** low risk, but a title like
`Graduate Engineer I, UK/I` would be ambiguous, so ticket 17 should keep it in view.

## Candidates dropped, and why

### Already covered by `sources.json` (1)

| Company | Reason |
|---|---|
| **Cloudflare** | Already present under `greenhouse`. Seed-list entry; dropped without probing. |

The dedup check was run programmatically over all 109 existing entries, per adapter, against
all 45 proposed slugs: **no other collision**. Note that the map's named UK producers
(Databricks, Palantir, Sierra, Intercom, Stripe, Anthropic, GitLab, and the rest) are all
already present and were never candidates here.

### Named seed companies dropped (9)

| Company | Sponsor status | Why dropped |
|---|---|---|
| **Google DeepMind** | No register row under "DeepMind" or "Google UK" — **Inference** only | `deepmind` on greenhouse is **live** (10 postings) but returned **0 UK postings** on 2026-08-01, and its titles are Google Gemini roles (`Distinguished Designer, Gemini App Systems`). Fails the UK bar. This was also the naive matcher's false positive — worth remembering. |
| **Darktrace** | `Darktrace Holdings Limited, Cambridge` — **Documented** | ATS is **Workday** (`darktrace.wd3.myworkdayjobs.com/DarktaceExternal`, per its careers page). Workday is *permanently* out of scope — [ticket 05](../../research/05-ats-platform-survey.md) rules it out for unauthenticated POST rather than GET. Clean, permanent drop. |
| **Revolut** | `Revolut Ltd, London` — Skilled Worker **and Scale-up** route — **Documented** | Careers page returned **HTTP 403** (bot protection); not bypassed, per constraints. No board found on any of the six adapters. **Highest-value miss on this list** — worth one manual look at where its apply links point. |
| **Starling Bank** | `STARLING BANK LIMITED, London` — **Documented** | No board on any of the six under `starlingbank`, `starling`, `StarlingBank`, `starlingbankltd`, `engineatstarling`. Careers page exposed no ATS host. |
| **Checkout.com** | `CHECKOUT LTD, London` is the likely entity — **Inference** | Careers page is a client-side search shell reporting **"0 Jobs found"** and exposes no ATS host. Its `/early-careers` page is topically ideal; the board is not reachable. |
| **ClearScore** | `Clear Score Technology Limited, London` — **Documented** | No board found on any of the six. |
| **Onfido** | `Onfido Ltd, London` — **Documented** | No board found on any of the six. Acquired by Entrust; an independent board may no longer exist. |
| **Cleo** | `Cleo AI Ltd, London` — **Documented** | The `cleo` greenhouse board **is live but is a different company** — 4 postings (`Product Manager`, `Sales Development Representative`, `Support Engineer I`), **0 UK**. Dropped deliberately rather than shipping a wrong-company slug. Cleo AI's real board was not located. |
| **Snyk** | `Snyk Limited, London` — **Documented** | `snyk` on Ashby returned `200` with **0 postings**. Fails the bar. Per ticket 05's rule a zero board is not evidence of a hiring pause — re-check later; do not add now. |

Seed companies **kept**: Monzo, Wise, Deliveroo, Octopus Energy, Improbable, GoCardless,
Tide, Zopa, Marshmallow, Multiverse — 10 of the 19 named seeds survived.

### Extensions probed and dropped (30+)

**Live board, zero UK postings** — fails the bar: Stability AI (`stabilityai`, gh, 4/0),
Tractable (`tractable`, ashby, 3/0), Form3 (`form3`, gh, 3/0), Mollie (`mollie`, ashby,
37/0), Trade Republic (`traderepublic`, gh, 1/0), Personio (`personio`, recruitee, 1/0).

**Live board, zero postings at all:** Bumble, Deel, Bolt, Optiver, Mistral AI.

**No board found on any of the six adapters** (slugs tried in the probe log): Thought
Machine, Depop, Ocado Technology, Curve, Moneybox, PrimaryBid, Wagestream, Featurespace,
Modulr, Fnality, Vinted, Klarna, XTX Markets, G-Research, Qube RT, DRW, Marex, Luminance,
Robin AI, Nscale, Signal AI, V7, Humanloop, Hugging Face.

## Two hazards the implementation ticket must not inherit blind

**1. SmartRecruiters cannot 404, so "no board" is weak evidence there.**
**Observed 2026-08-01:** a control request for the nonsense identifier
`zzzznotacompanyxyz` returned **`200` with `totalFound: 0`** — byte-for-byte the same shape
as a real company with an empty board. This is precisely the silent-zero hazard
[ticket 05](../../research/05-ats-platform-survey.md) warned about, now confirmed against a
control. Consequence: for every company probed only on SmartRecruiters, "not found" means
"not found at the identifier I guessed", **not** "has no SmartRecruiters board". Greenhouse,
Lever, Ashby, and Recruitee all returned honest `404`s.

Related: `Wise` and `wise` both returned the same 406 postings, so that identifier is
case-insensitive — but ticket 05 documents the identifier as the final segment of the
company's `careers.smartrecruiters.com/{identifier}` URL, and the existing inventory stores
`Visa` capitalised. Use **`Wise`** for consistency.

**2. Counts are a snapshot, and ticket 06 got burned by exactly this.** Its `lendingclub`
board verified with 14 jobs and returned `404` the same day. Every row here was
**re-verified in a single clean run** immediately before this file was written, so all 45
observations share one timestamp — but that timestamp is 2026-08-01. Re-run before editing
`sources.json`, and treat a first zero as a source-health event, never as evidence that all
of that company's Records are Closed.

## Proposed `sources.json` payload (research artifact — not an edit)

`sources.json` is **not** edited by this ticket; that is gated on
[the scan-time budget](../tickets/21-scan-time-budget.md). These are the 45 verified
net-new identifiers only, to be **merged into** the existing arrays, not to replace them.
The Wayve and Skyscanner entries below are the Ashby slugs — do not also add their Greenhouse
twins.

```json
{
  "greenhouse": [
    "graphcore", "sumup", "monzo", "mangroup", "isomorphiclabs", "tide", "physicsx",
    "grafanalabs", "gocardless", "complyadvantage", "canonical", "imc",
    "squarepointcapital", "typeform", "polyai"
  ],
  "lever": ["octoenergy", "zopa", "sonarsource"],
  "ashby": [
    "deliveroo", "faculty", "elevenlabs", "lendable", "trainline", "cohere", "wayve",
    "synthesia", "multiverse", "pleo", "motorway", "paddle", "marshmallow", "zilch",
    "oaknorth", "quantexa", "freetrade", "beamery", "skyscanner", "smarkets",
    "improbable", "griffin", "miro", "zego"
  ],
  "smartrecruiters": ["Wise"],
  "workable": ["withplum", "yapily"]
}
```

**Net-new feed count: 45** (greenhouse 15, lever 3, ashby 24, smartrecruiters 1,
workable 2, recruitee 0). Source Inventory **109 → 154**. Phased option: **31 Tier A**
first → 140 entries.

## Remaining uncertainty

- **No adapter publishes a directory of its customers**, so this list cannot be exhaustive.
  It is biased toward London fintech, UK AI/deep-tech, and quant trading, because that is
  where UK entry-level SWE/MLE hiring and sponsorship overlap most.
- **Recruitee produced nothing.** Zero UK candidates were found on it. That adapter may
  simply have negligible UK tech coverage; it is not evidence the fetcher is broken.
- **Register presence is a licence, not an offer.** Repeated because it is the single most
  tempting thing in this file to over-read.
- **Sponsor evidence for Man Group, IMC Trading, ComplyAdvantage, and Zego is weaker than
  the rest.** ComplyAdvantage and Zego are **Inference** on the brand→legal-entity link;
  Man Group and IMC Trading have **no register row found at all** under the names searched.
  For these four, sponsorship rests on **Inference**, full stop. Man Group and IMC are
  visibly running London graduate hiring today (per the Score table above) — but that is
  **relevance** evidence, not **sponsor** evidence, and it must not be read as the latter.
  These are the first four rows to prune if the list needs tightening. Cheapest way to
  upgrade any of them: find an explicit visa-sponsorship statement on the company's own
  careers or graduate-scheme page, which would make the row **Documented**.
- **Multi-adapter overlap with the Simplify feed is unmeasured**, exactly as ticket 06 left
  it. Measuring it correctly needs ticket 09's Cross-post rule, not company-name comparison.
- **Two boards are mid-migration** (Wayve, Skyscanner). Anything mid-migration can flip
  between survey and implementation.
