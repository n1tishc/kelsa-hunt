# Set notification UX at expanded source volume

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

How should qualifying Candidates be delivered once the source inventory expands:
one embed per Candidate, a digest, separate Score-band channels, or a capped hybrid?

The 105-board scratch scan produced 17 currently qualifying Candidates before the
notification-loss and Cross-post fixes. That is enough volume for the existing
one-embed-per-Candidate behavior to become noisy, but not enough evidence to choose a
digest policy blindly.

Set the delivery unit, batching window, ordering, daily cap, overflow behavior, and
whether Score Bands 10 and 5 deserve different urgency. Preserve the established rule
that notification is precision-first; never let a cap silently discard Candidates.

## Resolution

Resolved with the user on 2026-07-31 using the user's approved recommended defaults.
Use one Discord channel and one Notification Batch per scan; do not introduce a
cross-run timer or a second Score-band channel.

Presentation is adaptive:

- A Batch of one through five Candidates uses the existing rich embed per Candidate.
  The proven title link, company, strict-US location, source/reason footer, timestamp,
  and Score color remain unchanged.
- A Batch of six or more uses compact digest pages of at most ten Candidates. Each row
  contains a linked title, company, strict-US location, freshness/age, and Score. A
  17-Candidate expansion burst therefore arrives as two digest pages rather than 17
  rich embeds.
- Order every Batch by Score descending, Freshness Timestamp descending, then company,
  title, and stable `uid`. Score 10 appears before Score 5 and retains stronger visual
  emphasis, but both bands are delivered in the same scan; neither waits for a daily
  digest.

There is no daily hard cap. Overflow always continues onto another page, so volume can
change presentation but never discard a Candidate. Rate limits retain the bounded retry
policy.

Delivery is checkpointed per accepted page. After Discord accepts a page, stamp every
current member of its delivered Cross-post Groups and persist that state before sending
the next page. If a later page fails, accepted pages stay notified, undelivered pages
remain pending, and the run reports failure visibly. A crash between Discord acceptance
and persistence may cause a duplicate on retry; that at-least-once edge is preferable
to silently losing a Candidate.

Implementation scenarios must cover zero, one, five, six, 17, and more than ten
Candidates; mixed Score Bands; page-two failure; rate limiting; and a proven Cross-post
Group. Initial source-expansion Candidates use this normal policy rather than a special
seed or silent backfill path.

## Blocked by

- [Verify Discord delivery end-to-end](02-verify-discord-delivery.md) — confirm the
  actual embed presentation first.
- [Fix the two ways notifications get lost silently](03-fix-notification-loss.md) —
  batching must be designed on reliable delivery/state semantics.
- [Re-tune the notification threshold and age gate](04-threshold-and-age-gate.md) —
  those gates determine the real notification volume.
- [Decide how a Record is identified across many sources](09-dedup-across-many-sources.md)
  — measure volume after Cross-posts collapse.
