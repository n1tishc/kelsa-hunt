# Decision — Smart Inbox to reviewed packet interaction

**Question settled:** Can one owner understand and control the movement from a new
Smart Inbox item to a reviewed Application Studio packet, while retaining a bright
line between public deterministic classification and private advisory assistance?

**Prototype:** [`index.html`](index.html), a single self-contained file. Open it
directly in a browser; it has no server, dependencies, persistence, Vertex call, live
job-description request, or Career Profile content. All roles, profile fragments,
snapshot URLs, and outputs are deliberately synthetic.

## Surviving interaction shape

The prototype retained a single role-focused workspace with these explicit transitions:

1. A Smart Inbox row shows **two deliberately different signals** at once: the public
   deterministic Score and the private, advisory Fit Priority/explanation.
2. Selecting a row does not acquire a description. **Open or shortlist** is an owner
   authorization that creates one Selected Role Snapshot; shortlist remains a distinct,
   reversible owner choice.
3. The opened-role panel exposes the bounded Relevant Profile Context and evidence
   basis before packet review. It does not pretend to reveal or transmit a whole
   Career Profile.
4. The Role Analyst → Career Strategist → Application Writer → Evidence Critic results
   are four visible, synthetic, advisory stages. Evidence Cards label the supporting
   snapshot/profile pointers, while an unsupported observation is plainly a suggestion.
5. A packet requires explicit owner review before an outcome can be captured. Captured
   outcomes may inform an inspectable, resettable Working Preference Model, but never
   rewrite public facts or deterministic gates.

The persistent boundary notice and each action result say the same thing: no automatic
application, contact, public-notification change, or Deterministic Gate change occurs.
The guided boundary walkthrough makes this tangible by dismissing Fit Priority and
resetting the preference model while Score remains unchanged.

## Rejected variants

| Variant | Why it was rejected |
| --- | --- |
| A linear “apply now” wizard | It implied a submission endpoint and hid the owner’s review boundary. The product must never apply or contact autonomously. |
| Fit Priority as the inbox’s sole score | It blurred advisory private assistance with the public deterministic Score and made a private dismissal look like a candidate-policy change. |
| Automatic job-description retrieval on inbox arrival | It violated the selected-role boundary and obscured what opening/shortlisting authorizes. |
| A hidden multi-agent run with one final packet | It made context, evidence, and reviewability opaque. The owner needs four named, inspectable stage outputs. |
| A preference model that silently changes drafts | It removed owner control. Inspection and reset must be first-class, and learned preferences cannot overwrite facts or gates. |

## Follow-through

This validates the interaction and state shape only. Any production implementation
must implement the separate private-workspace data contract, use the public Canonical
Store read-only, preserve deterministic policy ownership, and retain the explicit
owner-triggered Selected Role Snapshot boundary.
