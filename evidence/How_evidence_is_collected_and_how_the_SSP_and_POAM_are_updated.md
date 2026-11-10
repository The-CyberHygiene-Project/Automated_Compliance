# How evidence is collected and how the SSP and POA&M are updated

**Status:** a description of one small reference system, written on 2026-11-10 from its documents and scripts. It is
not validated on any other system. Every statement below comes from a document or script I read; where I could not
confirm something it is listed in section 9. The scripts are in this folder (see [README.md](README.md)); redacted
examples of the evidence notes and a session record are in the `diwai` repository.

## 1. The documents that make up the record

| Document | What it is for |
|---|---|
| **SSP** (System Security Plan) | How each control is implemented. Has a revision history; every change adds a row ("2.18 amended N") that names the change record behind it. |
| **POA&M** | Open weaknesses, each numbered, with owner, plan and status. Has its own revision history in the same style. |
| **Self-assessment** | A table of every NIST SP 800-171A objective with one status word each (Satisfied, Partially satisfied, Other than satisfied, Unverified, Not applicable) and the evidence behind it. The score comes from this, not from the SSP. |
| **Evidence notes** (`DIWAI-EV-…`) | One note per piece of evidence: why it was gathered, how, what it showed. Raw output sits beside it. |
| **Change records** (`DIWAI-CR-YYYY-MM-NN`) | One per change to the system or the record: what changed, why, how to undo it, how it was verified, who approved. |
| **Procedures and logs** | Change authority, patch review (with a monthly log), a recurring-obligations schedule with a ledger of when each duty was done. |

## 2. Where evidence lives and how it is named

- **One canonical store** (a Nextcloud group folder) holds the controlled documents: SSP, POA&M, assessment, procedures, change records, evidence. A working copy is kept on the administrator's machine for editing.
- **Evidence notes** are named `DIWAI-EV-<AREA>-<YYYY-MM-DD>[-X]_<Title>.md`, where the area is a short code (for example AU audit, CM configuration, MP media, PS personnel, SC communications, VM server, MAC host). An older style (`EV_<area>_<control>_<date>`) also exists. A note opens with the system, the evidence type, who collected it, the method and the requirements it supports.
- **Raw output** is kept next to the note (for example `…-raw-<timestamp>.txt`), and, in the working folder, change-record evidence in a folder per change record.
- **Sub-folders** hold scan output (scan reports), training, personnel, physical access and marking evidence. The set also includes images and PDFs; I did not open them.
- **Change records** and the **patch review log** are separate documents, not folders of evidence.
- A dated record is treated as **immutable**: a change record from August that cites "SSP v2.15" is correct and is not repointed when the SSP moves on.

## 3. How evidence is collected

**By script (read-only, repeatable):**
- A host evidence run (`collect-mac-evidence.sh`) and the post-change checks.
- A **health monitor** that runs every 15 minutes on the server and reports whether controls are *running*, not only configured. It was written after four controls were found believed-running but stopped.
- **Scan publishing:** weekly mSCP results are published into the evidence folder (`publish-mscp-evidence.sh`), OpenSCAP reports are converted to PDF (`scap-report-to-pdf.sh`), and two vulnerability scans cover the server and the Mac.
- **Negative tests** that prove a control refuses what it should, and **drills** (correlation, media sanitization).

**By hand:** photographs and screenshots, physical-access and personnel evidence, interviews, signed training and attestation records.

**Rule applied to evidence:** a fix made earlier is not credit until a check run now, from the system itself, shows it working; where a control can fail silently, a negative test is included. A disputed value is reported at the *lower* value until a test removes the dispute.

## 4. From a finding to an SSP amendment and a POA&M revision

This is the path as the documents describe it. No single document lays it out step by step; it is assembled from the
session record of the August 2026 sweep, the method note in this repository, and the change-authority procedure.

1. **Find.** A sweep, a monitor alert, a scan or a review produces a finding. The August 2026 sweep checked each 800-171A objective against the *running system*, not against what the SSP said.
2. **Sort.** A finding is either corrected during the work or recorded as a POA&M item.
3. **Describe, then approve.** If a change is needed it is described first and the owner approves it in writing (a signed change record, or an approval recorded in the session).
4. **Change and verify.** The change is made (with an automatic undo for anything on an access path), then the check is run again.
5. **Record.** An evidence note, a change record, the re-determined rows in the self-assessment (the old status is kept in a note under the table with its date and reason), and the roll-up.
6. **Amend.** A row is added to the SSP revision history (and to the POA&M's if its content changed) naming the change record and stating whether the score moved.
7. **Publish.** The documents reach the canonical store only through the freshness gate (section 5).

## 5. Keeping the SSP and POA&M in step

- **A mutual version pin.** The SSP cites a specific POA&M version and the POA&M cites a specific SSP version. Bumping either without the other breaks the pair; the reference system recorded exactly that defect (the SSP cited a POA&M version that existed but had been superseded).
- **`doc-freshness.py`** refuses to publish a working copy that is behind or diverged from the canonical copy, and is the only route to the canonical store.
- **`xref-sweep.py`** finds live pointers that resolve but name a superseded version, skipping dated records on purpose.
- **`sweep-citations.py`** finds citations that do not resolve at all.
- **`count.py` / `assessment-status.py`** compute the roll-up from the self-assessment so a count is calculated, not typed. (They differ on how they treat "Not applicable"; see the README.)

## 6. Who drafts, approves and signs

- **Approval authority:** the system owner, in writing. **Implementer:** the owner, or an AI assistant acting at the owner's direction. The assistant implements only what the owner has approved, one described change at a time, and reports the result; if a control refuses an action it stops and reports. (Change-authority procedure.)
- **Drafting:** change records and amendment rows are drafted by the assistant or the owner. A change record carries a "Prepared by" and an "Approved" line; in at least one record the approval was entered by the assistant at the owner's explicit instruction, and the record says so.
- **Signing:** at the time of reading, the SSP's status was "Approved — Pending Signature". I cannot confirm any SSP revision was signed.
- **Independence:** the assessment is a self-assessment by the owner, operator and assessor. No independent review is claimed; the limitation is recorded as a risk.

## 7. What is scripted and what is manual

| Step | Scripted | Manual |
|---|---|---|
| Collect host and scan evidence | Yes (collection scripts, monitor) | Photos, screenshots, physical, personnel, training |
| Run negative tests and drills | Yes | A person starts them and reads the result |
| Re-determine objective statuses | No | Yes; owner or assistant edits the table |
| Compute the roll-up | Yes (`count.py`, `assessment-status.py`) | Choosing which rule to use |
| Update the SSP family table | No (the script's own note says it was hand-transcribed; whether that is still true was not confirmed) | Yes |
| Write the SSP and POA&M amendment rows | No | Yes |
| Write the change record and evidence note | No | Yes |
| Approve | No | Yes, the owner |
| Publish to the canonical store | Gate only (`doc-freshness.py`) | A person runs it |
| Check pointers and citations | Yes (`xref-sweep.py`, `sweep-citations.py`) | A person reads the output and fixes |
| Read monitor alerts | The monitor mails on change | A person must read the mail or a page; this was the reference system's weakest link |

## 8. What a small business would need to repeat this

Taken from what the reference system actually uses, not from a cost study:
- A **canonical store** for controlled documents and a **freshness gate** so a stale copy cannot overwrite it.
- A **self-assessment table** in a strict format (one bare status word per objective) and a **roll-up script** that lists any requirement it could not read.
- **Read-only evidence collection** for each host that saves output by date and ID, plus **scan publishing** into the evidence folder.
- A **health monitor** that detects a control silently stopping, **and a person or page that reads it**.
- **Templates** for change records (with an approval line and an undo), evidence notes and revision-history rows.
- A **version pin** between the SSP and POA&M and a pointer check after every version bump.
- A **recurring-obligations schedule and ledger**, and **negative tests** for controls that can fail silently.
- A named **approver** who is distinct, on paper, from whoever carries out the change. In a one-person business that separation is only on paper; say so in the plan.

## 9. Not confirmed

- The patch review procedure, the incident response plan and the policy-review checklist were not read for this note, so I cannot say how far they govern amendments.
- What is stored only on the server (logs, SIEM data) was not examined; the server was unreachable.
- The contents of the images and PDFs in the evidence folder were not opened.
- Whether the SSP family table is still transcribed by hand, and whether any SSP revision has been signed.
- Several scripts were read in part (marked in the README), so the descriptions of their inner logic are limited to what the headers and structure show.
