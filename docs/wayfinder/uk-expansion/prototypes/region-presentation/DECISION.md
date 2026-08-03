# Region Presentation Prototype — Decision Record

**Ticket**: [20 — Decide how region presents in Discord and on the ledger](../../tickets/20-region-presentation.md)
**Prototype**: `docs/wayfinder/uk-expansion/prototypes/region-presentation/`
**Date**: 2026-08-01

## Variants Tried

### Ledger default view

| Variant | Description | Verdict |
|---|---|---|
| **A — Mixed default, region column** | Both regions shown together, sorted by score. A "Region" column lets users filter. | ❌ Rejected — an unweighted mixed default buries the ~1,405 UK rows under ~10,418 US rows. Users who care about UK roles must click the column header to sort/filter, which is extra friction for the minority audience this feature serves. |
| **B — Default to US, UK click-away** | Page opens showing US only. UK is a tab or link at the top. | ✅ Accepted — the US view dominates by volume (~7:1), so defaulting to US preserves the existing user experience. UK users can click to see their region. |
| **C — Grouped by region** | Rows grouped under US and UK headers. | ❌ Rejected — takes more vertical space and duplicates the sort key. The click-away tab (Variant B) achieves the same separation more compactly. |

### Region in Discord embeds

| Variant | Description | Verdict |
|---|---|---|
| **1 — Region emoji in title prefix** | `🇬🇧 Software Engineer — Company` in the embed title. | ✅ Accepted — compact (costs 2 characters + emoji), visible at a glance, and works in both rich embeds (≤5 candidates) and paged digests. |
| **2 — Region as a field** | A dedicated "Region" field in the embed. | ❌ Rejected — costs a field slot (embeds max 25 fields, but we already use 2 for Company and Location). Also adds vertical noise for a low-signal piece of information. |
| **3 — Region in digest row** | `🇬🇧 Software Engineer — Company (Score 10)` in the compact digest row. | ✅ Accepted as fallback for paged digests (>5 candidates) where the rich embed isn't used. The emoji prefix is compact enough for the limited character budget. |

### Mixed batch ordering

| Variant | Description | Verdict |
|---|---|---|
| **Interleaved** | US and UK candidates sorted together by score/freshness (existing `_notification_sort_key`). | ✅ Accepted — the existing sort key already works correctly across regions. A UK candidate with Score 10 will appear above a US candidate with Score 5 regardless of region. |
| **Sectioned by region** | All US candidates first, then all UK candidates. | ❌ Rejected — artificially separates candidates that should compete on score. A UK Score-10 role should notify before a US Score-5 role, regardless of region. |

### Multi-region rows

| Variant | Description | Verdict |
|---|---|---|
| **One row tagged twice** | A `London; New York` posting appears once with both regions tagged. | ❌ Rejected — the ledger row identity is tied to the Opening Identity (dedup key). A multi-region posting is one opening, one row. Tagging it with multiple regions would require a multi-value region field that the current schema doesn't support cleanly. |
| **One row per region** | A `London; New York` posting appears once for US (with US locations) and once for UK (with UK locations). | ✅ Accepted — consistent with how `strict_region_record` already works. Each region's Derived View shows only the in-region locations. The dedup key is the same, so notifications are coordinated across regions. |

## Decision Summary

1. **Ledger**: Default to US, UK is a click-away tab.
2. **Discord rich embeds**: Region emoji prefix in title (`🇬🇧 title`).
3. **Discord digest rows**: Region emoji prefix in compact row.
4. **Batch ordering**: Interleaved by score (existing sort key).
5. **Multi-region rows**: One row per region in the Derived View, same dedup key.

## Open Questions

- The region emoji prefix in the embed title changes the title display in Discord's notification feed. This should be verified against Discord's rendering limits (250 characters for embed title).
- The click-away tab mechanism for the ledger requires a client-side implementation (the prototype demonstrates this with JavaScript tabs). The static Pages artifact will need a separate build step or a client-side JS file to implement the tab switching.
- Whether the region tag should also appear in the embed footer (alongside source and reason) for additional context. The prototype shows it in the title prefix only; the footer is an alternative worth revisiting if the title prefix proves too visually prominent.

## Prototype Usage

Run the prototype server:
```
python docs/wayfinder/uk-expansion/prototypes/region-presentation/server.py
```
Then open http://127.0.0.1:8765 in a browser. The server reads from the real `jobs.json` store and serves US, UK, and mixed views.
