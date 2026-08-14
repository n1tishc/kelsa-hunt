# Career Command Centre trial foundation

**Ticket:** [#27](https://github.com/n1tishc/kelsa-hunt/issues/27)
**Recorded:** 2026-08-14
**Status:** dedicated project and non-private foundation verified; private-data admission
remains blocked until the owner records the Vertex throughput quota and makes the
untracked local admission-facts file.

This is a non-secret operational fact sheet for the time-bounded Career Command Centre
experiment. It intentionally contains no credentials, private Career Profile material,
job descriptions, prompts, model outputs, or application data.

## Trial boundary

| Fact | Recorded value | Status |
| --- | --- | --- |
| Dedicated project | One newly created, otherwise empty dedicated trial project; its identifier remains in the owner's local Cloud controls | Verified 2026-08-14; created 2026-08-14 18:21:13 UTC |
| Billing | Linked to the owner's Google Cloud Free Trial billing account | Verified enabled |
| Trial credit | USD 300 remaining out of USD 300 | Owner verified in Cloud Billing on 2026-08-14 |
| Trial expiry | 2026-11-06 (the Billing UI exposes the date, not a precise time) | Owner verified in Cloud Billing on 2026-08-14; operational controls use an earlier safe date |
| Region | `us-central1` | Selected for the bounded Flash smoke test and reminders |
| Verified model | `gemini-2.5-flash` on Vertex AI | HTTP 200 synthetic request on 2026-08-14; 6 prompt / 29 total tokens; on-demand traffic |
| Model quota | Gemini-specific sustained-throughput value not established | Owner must inspect Vertex AI quota UI before sustained evaluation |

The synthetic model request used only `Return exactly FOUNDATION_OK`. It did not send
repository, job, profile, or application material. It proves the selected project and
region can call Flash; it does not prove a particular cost ceiling or sustained quota.

## Budget and trial exit controls

Two enabled, console-visible Cloud Scheduler jobs publish a non-private message to the
dedicated `career-command-centre-trial-reminders` Pub/Sub topic in `us-central1`:

| Milestone | Scheduler job | Scheduled time |
| --- | --- | --- |
| Export rehearsal | `career-command-centre-export-rehearsal-2026` | 2026-10-22 09:00 America/Los_Angeles |
| Shutdown | `career-command-centre-shutdown-2026` | 2026-10-27 09:00 America/Los_Angeles |

Those dates are 15 and 10 days before the confirmed expiry date. The cron expressions
would recur annually; pause both jobs after their 2026 execution. The topic has no
public subscription or endpoint. Cloud Billing budget setup remains an operational
follow-up; a budget is an alert, never a hard spending cap.

## Enabled APIs and empty-workspace check

The dedicated project has the foundation APIs enabled: Vertex AI, Cloud Run, Firestore,
Cloud Storage, Cloud Scheduler, Pub/Sub, Artifact Registry, Secret Manager, Cloud Build,
IAP, and Billing Budgets. Before those controls were added, the project had no Storage
bucket and Cloud Run was disabled; no application workload, private persistence, role
snapshot, Career Profile, or generated artifact has been admitted.

## Admission gate and known blocks

Before any private-data-bearing follow-up begins, the owner must:

1. inspect the Vertex AI quota UI and decide an evaluation cadence within the displayed
   Gemini Flash limit;
2. create an untracked local JSON file with the verified credit, expiry date represented
   as a conservative ISO-8601 operational cutoff, the two scheduled reminder timestamps,
   and `"reminders_retimed": true`; and
3. decide whether to configure a Cloud Billing budget alert for the dedicated project.

Keep the Career Profile, role snapshots, job descriptions, prompts, generated packets,
and production deployment out of this project until those conditions and the private
workspace data contract are complete. The public scanner, Canonical Store, deterministic
Candidate/Eligible Region/Score gates, and Discord delivery remain independent.

## Non-secret resource inventory

| Resource class | Present resources |
| --- | --- |
| Project | One dedicated, newly created trial project with billing enabled |
| Reminder infrastructure | One Pub/Sub topic and two enabled Cloud Scheduler jobs |
| Workloads and private persistence | None |

At shutdown, pause the Scheduler jobs, revoke any later runtime/deployment access,
verify no route can call Vertex, export and verify private data if any was admitted, and
delete the dedicated project. The local verified archive—not this project—is the
retained copy.
