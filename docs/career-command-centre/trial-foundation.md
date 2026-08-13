# Career Command Centre trial foundation

**Ticket:** [#27](https://github.com/n1tishc/kelsa-hunt/issues/27)
**Recorded:** 2026-08-13
**Status:** foundation established; private-data admission remains blocked on the owner
verifying the trial credit and exact expiry in Cloud Billing.

This is a non-secret operational fact sheet for the time-bounded Career Command Centre
experiment. It intentionally contains no credentials, private Career Profile material,
job descriptions, prompts, model outputs, or application data.

## Trial boundary

| Fact | Recorded value | Status |
| --- | --- | --- |
| Dedicated project | **Kelsa Hunt CC Trial** (full identifier retained only in the owner's Cloud Console and local `gcloud` configuration) | Active; created 2026-08-13 07:39:18 UTC |
| Billing | Linked to the owner's existing Free Trial billing account; billing enabled | Verified; no paid-continuation decision is implied |
| Trial credit and exact expiry | Not exposed by `gcloud` or the connected browser | **Owner must verify in Cloud Billing before any private upload** |
| Region | `us-central1` | Selected for the bounded Flash smoke test and trial reminders |
| Verified model | `gemini-2.5-flash` on Vertex AI | HTTP 200 synthetic request on 2026-08-13; 6 prompt / 19 total tokens; on-demand traffic |
| Model quota | No Gemini-specific throughput value was returned by the Service Usage API | Treat quota as unknown; inspect Vertex AI quota UI before sustained evaluation |

The synthetic model request used only `Return exactly FOUNDATION_OK`. It did not send
any repository, job, profile, or application material. A successful model request
proves the selected project and region can call the model; it does **not** prove a
particular ongoing quota, credit balance, or cost ceiling.

## Budget and trial exit controls

The Cloud Billing budget `Kelsa Hunt CC Trial monthly guardrail` is scoped only to this
project and is set to **USD 60/month**. It notifies the billing-account's default
recipients at 50%, 80%, and 95% of current spend, plus 80% forecast spend. A budget is
an alert, not a hard spending cap and not authorization for a paid continuation.

Two enabled, console-visible Cloud Scheduler reminders publish a non-private message to
the dedicated trial-reminders topic in `us-central1`:

| Milestone | Scheduler job | Provisional scheduled time |
| --- | --- | --- |
| Day 75: export rehearsal | Dedicated export-rehearsal Scheduler job | 2026-10-27 09:00 America/Los_Angeles |
| Day 80: shutdown | Dedicated shutdown Scheduler job | 2026-11-01 09:00 America/Los_Angeles |

These dates are calculated from the dedicated project's 2026-08-13 creation date, not
from an unverified billing expiry. Once the owner confirms the actual trial end date,
move both jobs earlier if necessary and pause them after their 2026 execution (their
cron schedules recur annually). The topic has no public subscription or endpoint.

## Enabled APIs

The dedicated project has only the required foundation APIs (and Google-managed
dependencies) enabled:

- `aiplatform.googleapis.com`
- `run.googleapis.com`
- `firestore.googleapis.com`
- `storage.googleapis.com`
- `cloudscheduler.googleapis.com`
- `artifactregistry.googleapis.com`
- `secretmanager.googleapis.com`
- `cloudbuild.googleapis.com`
- `iap.googleapis.com`
- `billingbudgets.googleapis.com`

No Cloud Run service or job, Firestore database, Cloud Storage bucket, Artifact Registry
repository, Secret Manager secret, or private workspace data exists yet.

## Identities and deployment trust

Four user-managed service identities exist with no downloaded keys:

| Identity | Intended single purpose | Current access |
| --- | --- | --- |
| UI runtime identity | Future IAP-protected UI runtime | No application role yet |
| Job runtime identity | Future isolated scheduled-job runtime | No application role yet |
| Scheduler identity | Future Cloud Scheduler invoker | No application role yet |
| Deployer identity | GitHub Actions deployment identity | May be impersonated only through the restricted federation below; no deploy role yet |

The active Workload Identity Federation provider is:

- Pool: one global Career Command Centre GitHub federation pool
- Provider: one provider for this repository's `main` branch
- Issuer: `https://token.actions.githubusercontent.com`
- Condition: repository must equal `n1tishc/kelsa-hunt` **and** ref must equal
  `refs/heads/main`.
- The mapped repository principal can impersonate only the dedicated deployer identity
  through `roles/iam.workloadIdentityUser`.

No service-account key was created or downloaded. No GitHub secret, external public
endpoint, runtime identity role, or deployment permission is required or granted at
this foundation stage.

## Admission gate and known blocks

Before Ticket #30 or any private-data-bearing follow-up begins, the owner must open
Cloud Billing for this billing account and record the actual Free Trial credit balance
and expiration date. Update the two reminder jobs against that confirmed date. Also
inspect the Vertex AI quota UI for the desired evaluation cadence; the API verifies
Flash access but did not return a Gemini-specific throughput limit.

Keep the Career Profile, role snapshots, job descriptions, prompts, generated packets,
and production deployment out of this project until that verification and the private
workspace data contract are complete. The public scanner, Canonical Store, deterministic
Candidate/Eligible Region/Score gates, and Discord delivery remain independent.

## Non-secret resource inventory

| Resource class | Present resources |
| --- | --- |
| Project | One dedicated, labeled Career Command Centre trial project (identifier retained only in owner controls) |
| Billing guardrail | One project-filtered USD 60/month budget |
| Reminder infrastructure | One Pub/Sub topic and two Cloud Scheduler jobs |
| User-managed service accounts | One each for UI runtime, job runtime, Scheduler, and GitHub deployment |
| Federation | One GitHub OIDC provider, restricted to this repository's `main` branch |
| Workloads and private persistence | None |

At day 80, the shutdown order is: pause Scheduler jobs, remove the GitHub federation
binding/provider, disable or remove runtime identities and any later secrets, verify no
route can call Vertex, export and verify any private data, then delete the dedicated
project. The local verified archive—not this project—is the retained copy.
