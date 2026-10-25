# Keeping the record true (maintainer's method)


The assessor in this repository reads a record and judges it. This note covers the other half: how the owner keeps
that record true after the first assessment, so the next assessment starts from facts.

## The rule

**A status changes only when evidence changes, and the old status stays visible.**

1. **One status per objective, bare.** The status cell holds one word (Satisfied, Partially satisfied, Other than
   satisfied, Unverified, Not applicable) and nothing else. Anything extra in the cell makes a parser skip the row
   without an error. A counter must therefore list the requirements it found *no rows* for, so a skipped row is
   loud.
2. **Superseded determinations are kept** in a note under the table (date, old status, why it changed). The
   history is the audit trail.
3. **A disputed value is reported at the lower value** until a test removes the dispute.
4. **Re-determine on live evidence.** A fix that was made earlier is not credit until a check run now, from the
   system itself, shows it working. Where a control can fail silently, include a negative test (a bad password is
   refused; a blocked port is blocked).
5. **Requirement is met only when every objective is Satisfied or Not applicable.** The roll-up is computed by a
   script from the record, never typed. The summary tables in other documents are copied from that output.

## The maintenance loop

| Step | What happens | Who |
|---|---|---|
| Pick | One requirement, from the to-do list ordered by effort | Owner approves |
| Check | Read-only commands and the documents; record what was seen | AI or maintainer |
| Describe | If a change is needed, describe it first | Maintainer writes, owner approves |
| Change | Run it with an automatic undo for anything on an access path (firewall, logins, authentication) | Maintainer |
| Verify | Re-run the check; note anything that only shows up after time passes and put its date in the schedule | Maintainer |
| Record | Evidence note, change record, re-determined rows, roll-up, dashboard, search index | Maintainer |

Three tiers of AI help follow the same split: **observe** (read-only, names what to do), **repair** (a pre-approved
fix that needs a hardware-key approval), **change** (anything new: described by the owner, approved, then run).
A local model works in the first two. Anything not already approved is a change.

## What the tools do and do not do

- The **assessor and grader** in this repository are read-only on the record.
- The **roll-up** (see `rollup.py` when added) turns the record into per-requirement and per-family counts and
  prints every requirement it could not read.
- Editing the record in place is a maintainer's job and is kept separate from the read-only tools, so a mistake in
  an assessment run can never rewrite the owner's record.

## Documents live in one place

Keep one canonical copy of each controlled document. Working copies drift silently, so a freshness check compares
them with the canonical copy, and a new or changed document is published through that check, not by copying.
Use an editor that preserves the file exactly: some web editors reformat tables and delete text when they save.
