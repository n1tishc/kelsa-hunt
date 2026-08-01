# Verify Discord delivery end-to-end

<!-- wayfinder:task -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

Nothing to decide — this unblocks trusting every alerting decision downstream.

`post_discord` has **never made a successful call**. The `--seed` run marked all 23
then-current matches notified without sending (that is what seeding does), and all 7
scheduled runs since had zero qualifying rows. Runs report `success` and the
`DISCORD_WEBHOOK` secret exists, but delivery itself is unverified inference.

Send exactly one embed and confirm it lands in the channel.

**Do it against the scratchpad copy of the store, not the real one**, so notification
state can't be corrupted by a test.

⚠️ Do **not** test via `job_alert.py query --notify`. `cmd_query` hands *all* matching
rows to `post_discord`; `--limit` only bounds the printed output. `query --min-score 3
--all --notify` would fire several hundred embeds at the channel.

Record in the answer: that an embed arrived, how it rendered (title/company/location/
colour/footer), and anything about the embed format worth changing before volume grows.

## Resolution

Resolved 2026-07-30. The Discord API accepted exactly one embed (HTTP 204) from
`post_discord`, sent using a scratchpad copy of the Canonical Store, and the user
confirmed that it visibly arrived in the target Discord channel.

The delivered embed was:

- Title: `Engineer 1 New Grad - Data Scientist`
- Company: `Crowdstrike`
- Location: `Sunnyvale, CA`
- Colour: green (`#2ECC71`)
- Footer: `Simplify • explicit new-grad, junior-level marker`

The real Canonical Store and private annotations were not modified. Delivery itself is
now proven; future silence means no Candidate cleared the active gates unless a later
run reports a source or notification failure.

## Blocked by

_(nothing — frontier)_
