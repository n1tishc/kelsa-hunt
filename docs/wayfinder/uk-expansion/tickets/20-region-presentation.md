# Decide how region presents in Discord and on the ledger

<!-- wayfinder:prototype -->
Parent: [Map: UK roles alongside US in kelsa-hunt](../map.md)

## Question

What does a two-region Public Job Ledger and a two-region Discord alert actually look like,
given the ledger is a static allowlisted artifact with no server behind it?

The charted decision is one ledger with a region column and a filter, and one Discord feed
with a region tag per Candidate — deliberately not two dashboards and not two webhooks. This
ticket makes that concrete enough to react to before it ships.

### What must be settled

- **Ledger default view.** Does the page open showing both regions mixed, or default to one
  with the other a click away? At current volume the visible view is ~10,418 US Records
  against ~1,405 UK — so an unweighted mixed default buries the UK rows you added this map to
  see.
- **The filter mechanism.** The ledger is a strict-US-today static artifact served from
  GitHub Pages with no backend; region filtering must be client-side over the deployed data,
  or baked into separate pre-rendered payloads. Which, and does it change the deployment
  artifact's shape?
- **Region column versus region grouping.** A column sorts and filters; grouping reads
  better at a glance. Prototype both rather than arguing about it.
- **Multi-region rows.** Whatever
  [the Eligible Region boundary](15-eligible-region-boundary.md) decides about a
  `London; New York` posting has to render — one row tagged twice, or one row per region.
  The prototype should show the chosen shape, not dodge it.
- **Discord embeds.** `build_embed()` and `build_digest_embed()` produce rich embeds for ≤5
  Candidates and paged digests above that. Where does region go — a title prefix, a field, an
  emoji flag, the embed colour? `color_for(score)` currently encodes Score in colour, so
  colour is taken. Digest rows are compact (`_compact_digest_row()`), so a region tag costs
  scarce characters there.
- **Mixed batches.** A single scan can produce US and UK Candidates together. Does the digest
  interleave them, or section by region? `_notification_sort_key()` defines the existing
  order.

### Constraints

- The ledger stays **public, allowlisted, and job-data-only**. No `annotations.json` state,
  no applied/hidden — both permanently ruled out.
- Generated dashboard data stays **ephemeral**, never committed — settled by
  [the dashboard shape ticket](../../tickets/10-dashboard-shape.md).
- Python stdlib only; no server; Pages publishes via the existing `job-alert` workflow, not a
  Jekyll or Static HTML starter.

### Deliverable

A throwaway prototype under `docs/wayfinder/uk-expansion/prototypes/`, following
[the job-ledger prototype](../../prototypes/job-ledger-prototype/) — enough to click through
real Store data in both regions and pick a variant. Link it from this ticket rather than
pasting screenshots. Record which variants were tried and why the loser lost.

## Blocked by

- [Define the Eligible Region boundary](15-eligible-region-boundary.md) — there is nothing to
  render per region until region resolution and multi-region row identity are settled.

## Related work

- [Prototype the dashboard and decide how it gets its data](../../tickets/10-dashboard-shape.md)
  — established the US-only spreadsheet ledger this extends.
- [Set notification UX at expanded source volume](../../tickets/13-notification-ux-at-expanded-volume.md)
  — the ≤5 rich / paged-digest rule a region tag has to fit inside.
- [Decide whether an Excel export survives the dashboard](../../tickets/11-does-excel-survive.md)
  — Excel was cut; the ledger owns the read-only archive.
