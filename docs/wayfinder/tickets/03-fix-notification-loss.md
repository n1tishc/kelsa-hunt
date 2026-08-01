# Fix the two ways notifications get lost silently

<!-- wayfinder:task -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

Nothing to decide — two known defects that make alerts vanish without any signal. Both
must be gone before notification-tuning decisions mean anything, because until they are,
"I didn't get pinged" is ambiguous between "nothing matched" and "it broke quietly."

**1. `post_discord` reports success after a failed send** — `job_alert.py:465-468`.
A non-429 `HTTPError` prints to stderr, `break`s, and the function still returns `True`.
The caller then stamps `notified_at` on every row, so those roles are never retried. A
revoked or wrong webhook silently converts "no alerts yet" into "no alerts ever." Note
the asymmetry: an *empty* webhook returns `False` and is safe; a *broken* one is not.

**2. Dedup discards notification state** — `Store.candidates()` returns deduped rows, but
`cmd_scan` stamps `notified_at` only on the surviving uid of each dedup group. Collapsed
twins stay un-notified forever and can re-fire later depending on iteration order.
Evidence found while diagnosing: Quora "Machine Learning Engineer New Grad", Gen Digital
"AI & ML Engineer 1", and xAI "Member of Technical Staff" all sat un-notified at exactly
21 days and then aged out of the window entirely, unseen.

Fix both, and record in the answer whether the fix changes what `candidates()` returns
(it should not — only what gets stamped).

## Blocked by

_(nothing — frontier)_
