# Decide whether an Excel export survives the dashboard

<!-- wayfinder:grilling -->
Parent: [Map: Kelsa-hunt as one coherent tool](../map.md)

## Question

Is there a job the spreadsheet does that the dashboard won't — and if so, what exactly?

The Excel sheet was requested as a first instinct ("get the data out of JSON"), and the
owner is explicitly open to the dashboard replacing it. So this ticket exists to kill the
feature or to justify it, not to schedule it.

Note the tool **already has** `job_alert.py export` writing SQLite for ad-hoc SQL, so
"structured data I can query" is a solved problem. The unmet need, if any, is narrower —
probably one of:

- Hand-editable columns the tool doesn't own (status, notes, follow-up dates). But that
  makes the sheet **private data** under ADR-0001 and it can't be committed — which is a
  different feature than an export, and belongs to the fog entry "Day-to-day
  applied-tracking workflow."
- Offline/portable viewing without the dashboard
- Pivot-table analysis the dashboard won't offer

Resolve to one of: **cut it** (fold into the dashboard), **read-only derived export**
(regenerated per run, committed, never hand-edited), or **private working sheet** (
gitignored, and then it's really an applied-tracking question).

Answering "cut it" is a success, not a failure — record the reasoning either way so it
doesn't get re-raised.

## Blocked by

- [Prototype the dashboard and decide how it gets its data](10-dashboard-shape.md) — can't
  judge what the dashboard fails to cover before seeing it.

## Resolution

Resolved with the user on 2026-07-31: **cut the Excel export**.

The spreadsheet was requested to provide a searchable, durable record outside raw JSON.
The resolved dashboard now does that directly: it is a read-only US job ledger with full
history, search, and filters. A regenerated Excel copy would duplicate the same Derived
View, add another artifact and validation path, and provide no identified workflow value.

Offline access and pivot-table analysis are not current requirements. Manually editable
notes, application status, and follow-up dates would be private annotations rather than
an export; if that need becomes concrete, address it through the separate private
applied-tracking workflow without changing this decision.
