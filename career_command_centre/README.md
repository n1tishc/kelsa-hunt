# Private Smart Inbox vertical slice

This is Ticket #31's deployable-but-not-yet-deployed private workspace. It renders a
read-only, request-scoped view of recently eligible/open public Records and preserves
the public scanner as the only authority. It has no mutation endpoint, Firestore,
Storage, Vertex call, local persistence, Career Profile input, application action, or
Discord integration.

Each row intentionally shows two unrelated signals:

- **Deterministic Score** comes from the exact shared candidate policy in `job_alert.py`.
- **Fit Priority** is advisory. Until the Ticket #27 admission facts are recorded, it
  remains a visible safe-review state and no private/model request is made.

“New” means a currently eligible, open Record first observed by the public Canonical
Store during the configured seven-day review window. This is intentionally not an
eligibility-history claim: Candidate is computed at query time, and recording every
non-candidate to infer historical reclassification would create the prohibited private
mirror. A future owner-authorized, bounded inbox-state implementation may add an
explicitly documented reclassification review, but it may not copy the Canonical Store.

## Local preview

Use a public, local `jobs.json` only:

```sh
SMART_INBOX_OWNER_EMAIL=owner@example.com \
SMART_INBOX_CANONICAL_STORE_URL=https://raw.githubusercontent.com/n1tishc/kelsa-hunt/main/jobs.json \
SMART_INBOX_IAP_AUDIENCE=IAP_OAUTH_CLIENT_ID.apps.googleusercontent.com \
gunicorn --bind :8080 career_command_centre.wsgi:application
```

This is a Cloud Run/IAP entrypoint, not a local browser server: it requires a signed IAP
JWT for the configured audience and then checks the verified email against the owner.
Production must enable IAP directly on the Cloud Run service and grant the IAP Web App
User role only to the owner. A supplied `X-Goog-Authenticated-User-Email` header alone
never authenticates a request.

## Deployment hold

Do not deploy this container or upload private data until the owner has recorded the
actual Free Trial credit/expiry, retimed the day-75/day-80 reminders, and inspected the
Vertex quota as required by [the trial foundation](../docs/career-command-centre/trial-foundation.md).
At deployment time, set `SMART_INBOX_OWNER_EMAIL` and the public,
read-only `SMART_INBOX_CANONICAL_STORE_URL`; no credential is needed for that public
source. The Cloud Run service must not allow unauthenticated access.
