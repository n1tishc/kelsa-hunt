# Survey which ATS platforms expose usable public job APIs

<!-- wayfinder:research -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

Beyond Greenhouse, Lever, and Ashby, which applicant-tracking systems can this tool fetch
from with a plain unauthenticated HTTP GET returning JSON — and which can't?

The three existing fetchers are ~25 lines each because those platforms publish clean board
APIs. Any platform that needs auth, HTML scraping, or a headless browser is a categorically
different cost, and that difference should drive whether it's worth supporting at all.

For each candidate platform, establish:

- The public board endpoint URL pattern and how the per-company slug is derived
- Whether it returns JSON without auth, and whether it rate-limits
- What fields come back — critically **location** and **posted date**, which the age gate
  and Bay Area filter depend on. A platform that omits location is close to useless here.
- Roughly which notable Bay Area tech companies use it

Candidates to cover at minimum: **Workday** (widely used, notoriously awkward),
**SmartRecruiters**, **Rippling**, **Workable**, **Recruitee**, **BambooHR**,
**Teamtailor**, **JazzHR**. Add any others found.

Deliver a ranked table: platform → effort to support → Bay Area company coverage gained.
The ranking matters more than exhaustiveness — it's what the budget ticket consumes.

Note: `README.md` already warns that companies migrate between ATSs and a configured slug
can silently start returning zero. Flag anything that makes that worse.

## Blocked by

_(nothing — frontier)_

## Resolution

Research completed 2026-07-30:
[ATS Platform Public API Survey](../research/05-ats-platform-survey.md).

The survey recommends SmartRecruiters, Workable, and Recruitee as low-complexity
GET/JSON integrations. Workday is the only high-coverage exception worth revisiting,
but its public search requires POST and therefore falls outside this ticket's transport
boundary.
