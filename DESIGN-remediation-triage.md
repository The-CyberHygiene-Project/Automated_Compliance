# Design note: remediation triage (draft for comment)

**Status:** steps 1 and 2 are built ([`triage.py`](triage.py), [`poam.py`](poam.py)); steps 3 and 4 are not. Nothing here changes the assessor, the allow-list or any host.

## Why

The assessor produces a list of objectives that are Unmet, Not checkable, or have an undefined organization-defined parameter (ODP). That list is a to-do list, but a mixed one: some items need a decision, some need a paragraph in a document, some need a setting changed on a host, and some need a person with a clipboard. Treating them alike wastes effort and invites a local model to invent a "fix" for something that is not a configuration problem.

This note describes a **second, narrower loop** that sorts the list, tracks each fix as a checkable unit, and exports a durable record. It never applies anything to an assessed system.

**Positioning.** Like the rest of this project, this is a reference design for very small businesses, not a production remediation service. A person decides; the tool sorts, drafts and records.

## Principles

1. **Lead, don't apply.** Nothing in this loop writes to an assessed host. The assessor's read-only allow-list is not reused for anything except the *verify* step, after a person has applied a change.
2. **A document fix and a configuration fix are done differently.** A document fix is done when the text states the fact and a person merges it. A configuration fix is done only when **the same read-only probe that failed the assessment now succeeds**. The record must carry that difference, or the loop will close items the host does not satisfy.
3. **The drafter never judges.** Only a later assessment run may mark a fix re-assessed (Met or Unmet). The model that drafted a change is not the one that decides it worked.
4. **A person accepts.** Acceptance is the only transition from draft to open.
5. **Sort first, with code.** Classification should be deterministic wherever the data already says which class an item is. A model is used only where the data cannot decide.

## Step 1: sort every open item into one of four classes

| Class | How it is recognised | What the fix is |
|---|---|---|
| **Parameter gap** | The kit marks the objective as an ODP and no value is defined | A decision: a value sized to the organization, accepted by a person. The Rev 3 rule stands: Met only when a document quotes the actual value. |
| **Document gap** | The control may be operating, but the policy, plan or record does not say so; or `--strict` correctly refused to treat a policy as proof of implementation | Draft or patch the document from evidence the assessor already quoted. |
| **Configuration gap** | A read-only probe showed the setting absent or wrong | A change unit (below). |
| **Not checkable** | Interviews, physical inspection, training attendance; recorded as Not checkable | The question to ask and the evidence a person must collect. It can never become Met because a draft procedure exists. |

The first and last classes come straight from fields the runner already records. The document/configuration split uses the strict-mode result and whether the evidence is a host command output or a document quote. Anything the rules cannot place is listed as **unsorted** for a person; it is not guessed.

**First deliverable:** a small script that reads the finished register and writes the sorted list, with counts per class. No model is needed for this step.

## Step 2: the change unit (configuration gaps only)

A non-documentary fix is a unit with a probe, a desired state and a verification command, not a paragraph. One file or one JSON object, the same fields every time:

- **Objective id** and the evidence quote. The unit exists because that probe failed.
- **Component:** host, service or role.
- **Current state:** the command run and the output that made it Unmet, copied from the assessment record.
- **Desired state:** one checkable sentence a re-run must observe.
- **Change:** a unified diff against the file the probe already showed, or a declarative snippet. No prose in place of the diff.
- **Blast radius:** what else the setting affects, in particular availability of the one server a very small shop has.
- **Apply step:** the command a person will run. Written out, never executed by the tool.
- **Verify:** the same allow-listed read-only command the assessor used, and the output that counts as Met. If no such command can be named, it is not a configuration unit.
- **Rollback:** the reverse diff or the previous value.
- **Status:** `draft`, `accepted`, `applied`, `reassessed-met`, `reassessed-unmet`. Only an assessment run sets the last two.

**Configuration versus architecture.** A configuration unit is one component, one setting, reversible. An architecture item (more than one component, or a boundary change) is a short design note plus an ordered list of configuration units; it is not one patch and never becomes Met itself. A configuration miss must not be promoted into an architecture rewrite. An architecture item exists only when the objective cannot be met by a setting on the current component, or meeting it would move the authorization boundary. If the fix needs a new host, network or identity store, the unit stops at the decision and the first reversible step.

## Step 3: a bounded drafting round (optional, later)

If the sorted list shows enough configuration gaps to justify it, a local model may draft the unit. The discipline matches the assessor: one item, fresh context, a completeness check, no secrets.

- **Input:** one objective, its requirement text, the failed probe and output, the retrieved file (if any), the size band, and any ODP already set. Never the whole register.
- **Output:** a fixed shape; a round with a missing field is rejected, as `record_results` rejects an incomplete assessment.
- **Rejected automatically:** a verify command not on the allow-list; a diff not against the retrieved file; any pipe, redirect, substitution, chain or write; any request to read hashes, keys or stored credentials.
- **Tools:** editing tools on a review copy of the documents and the unit files only. No SSH write path.
- **Expected failure mode:** the model measured here leans lenient on assessment and will lean helpful on remediation (plausible settings, generic policies, milestone dates that ignore a one-person shop). The human accept step is the control, not a better prompt.

Model choice, context size and sampling settings are **not fixed by this note**; they are to be measured on the reference machine, in the same way the assessment model was.

## Step 4: provenance

Every draft carries the AIBOM data the project already generates: model id, prompt fingerprint and run tag. A draft without that is easy to mistake for an approved change.

## Step 5: OSCAL as the durable record

The spreadsheet stays the working view. The durable record is an OSCAL POA&M built from the same rows.

- Each item has a title, the weakness in plain language, the related control id, a link back to the assessment finding or observation, milestones with dates, and a status.
- Milestones can be coarse: "ODP value accepted", "document merged", "change applied on the reference host", "re-assessed".
- Deviations (operationally required, risk adjustment, false positive) and vendor dependencies belong in the same item so a later assessor can see why it stayed open.
- The register already distinguishes cells the AI wrote from cells a person edited; the exporter keeps that distinction in the remarks.
- An accepted ODP set can also be written into an OSCAL profile, so the next assessment imports the values instead of rediscovering them.
- A desired state, once re-assessed Met, is what a component definition may claim. Until then it must not claim the control is satisfied.

**Second deliverable:** the POA&M exporter. It is more useful than generating configurations and carries less risk.

## What is deliberately out of scope

- Any automatic apply, including a write allow-list that runs unattended.
- Reusing the assessor's command channel for anything but the verify step.
- A model deciding configuration versus architecture, setting an ODP, or writing the POA&M without a person accepting it.
- Platform-specific content. The units are written against whatever the profile says the organization runs; this note names no product.

## Build order

1. Triage script: register in, sorted list and counts out. (No model.)
2. POA&M exporter from the same register.
3. Change-unit format and its validator (rejects unlisted verify commands, non-diff changes, missing fields).
4. Optional drafting round, only if step 1 shows configuration gaps worth the effort.

Each step is test-first, and the suite stays green before the next begins.
