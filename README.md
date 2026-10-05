# Automated_Compliance

A **local AI assessor** for NIST SP 800-171A, with a human in control.

It reads an organization's own compliance documents, checks a server with read-only commands, and records a
status and its evidence for every assessment objective. The AI makes the judgments. A small runner around it
hands over one requirement at a time, enforces what the AI may do, and checks that the record is complete.
Everything runs on one Mac with a local model: no assessment text leaves the machine.

> **Status: early.** One real requirement has been assessed end to end on Rev 3, and a full run is in progress.
> The method works; the results are not yet validated. Treat everything here as a working tool, not an
> assessment authority. It does not say what a contract requires, and it is not legal advice.

## Why this exists

Assessing a system against 800-171A means judging 300-plus objectives with evidence. Much of that evidence is
in documents (policies, plans, records), and some is on the system itself. A local model can read both. The
open questions are whether it judges well, and whether it can be kept safe while it does. This repository is
the test harness for both questions.

## How it works

1. **One requirement per round, fresh memory.** The model gets a requirement and its objectives, then looks
   for evidence with tools: run a read-only command on the server, search or read the documents, and finally
   `record_results` for every objective.
2. **An approved list of read-only commands runs on its own.** Reads of secrets (password hashes, private
   keys, stored credentials) are refused. Anything else is declined, or put to a person with `--ask`.
   Pipes, redirects and command chains never run unattended.
3. **A sandbox around the whole thing.** The AI can reach only the local model server and one SSH connection.
   Answer keys, notes and other folders are unreadable to it.
4. **The runner checks the record.** Every objective needs a status (Met, Unmet, N/A, Not checkable), a source
   and evidence. A short or malformed record is sent back, never accepted.
5. **A grader compares with your own key.** The key is yours and stays outside the repository.

More detail in [METHOD.md](METHOD.md). What went wrong along the way, and the fixes, in
[LESSONS.md](LESSONS.md).

## Rev 2 and Rev 3

| | Rev 2 (800-171A, 2018) | Rev 3 (800-171A Rev 3) |
|---|---|---|
| Requirements | 110 | 97 |
| Objectives | 320 (297 lettered, 23 single) | 510 (422 objectives + 88 parameters) |
| Kit | `objectives.md` | `kit-r3/objectives.md`, built mechanically from NIST's OSCAL catalog |
| Answer key | your own self-assessment | a *provisional, derived* key (see METHOD.md) |

Rev 3 adds **parameter objectives**: each organization-defined value (a time period, a frequency, a list) must be
defined. The AI marks such an objective Met only when a document states the actual value, and quotes it. The
unmet ones become a to-do list for the organization.

## What is in the repository

| Path | What it is |
|---|---|
| `assess.py` | The runner: one requirement per round, tools, memory budget, completeness check |
| `allowlist.py` | The read-only command list and the refusal rules (heavily tested) |
| `assess.sh`, `host`, `sandbox.sb` | The launcher, the AI's single path to the server, the sandbox profile |
| `grade.py`, `grade_r3.py` | Graders for Rev 2 and Rev 3 |
| `key_r3.py` | Builds the provisional Rev 3 key from your Rev 2 results and NIST's mapping |
| `fill_register.py` | Writes results into a copy of the Rev 3 measurement register (below) |
| `templates/NIST_800-171r3_Measurement_Register.xlsx` | **A blank Rev 3 measurement register** (see below) |
| `objectives.md`, `kit-r3/` | The objective lists (NIST data, generated mechanically) |
| `objectives.lettered-only-297.md` | An earlier Rev 2 list that lacked the 23 single-objective requirements; kept for comparison |
| `reference/` | Kit generator, spreadsheet reader, and `fetch_nist_data.sh` for NIST's files |
| `aibom/` | **AI Bill of Materials** for the reference run: model, file hashes, settings, prompts, software, data (`AIBOM.md`, CycloneDX `aibom.cdx.json`) and `make_aibom.py` to generate your own |
| `tests/` | Automated tests; none of them touch a model or a server |

## The measurement register (a spreadsheet you can use without any of the code)

`templates/NIST_800-171r3_Measurement_Register.xlsx` is a blank, generic workbook built from NIST's OSCAL
data for SP 800-171 Rev 3 and SP 800-171A Rev 3 (catalog version 1.1.0). It is not applied to any organization.

| Sheet | What it holds |
|---|---|
| Requirements | The 97 requirements, with owner, implementation status, evidence location and notes to fill in |
| **ODPs** | The 88 organization-defined parameters (time periods, frequencies, lists). **Define these first**: many objectives cannot be judged until their parameter is |
| Objectives | The 422 assessment objectives: result (Met / Not Met / N/A), method, evidence, assessor, date |
| Methods, Withdrawn, Summary | NIST's suggested methods, the 33 withdrawn numbers and where they went, and live totals by family |

Dropdowns and colors are built in (green Met, red Not Met, grey N/A, yellow still waiting). Its Rev 2 ID
column is empty on purpose: `key_r3.py` and `fill_register.py` can fill it from NIST's Rev 2 to Rev 3 mapping,
and can write an AI scan's results into a copy. Always work on a copy; never put real findings in the template.

## AI Bill of Materials

`aibom/AIBOM.md` records exactly what produced the reference results, so others can reproduce or question them:
the model (name, quantization, where the files came from, a SHA-256 for every file), the settings (temperature,
context, step and memory limits), a fingerprint of the instructions the model receives, the software and
hardware, and the data it was given. `aibom/aibom.cdx.json` is the same in CycloneDX 1.6 for tools that read it.
It covers the Gemma 4 26B run; an early trial with another model is not part of it.

Making one for your own setup:

```
python3 aibom/make_aibom.py --model-key <LM Studio model id> --model-dir <folder with the model files> --source <where you got them>
```

It records no folder paths, serial numbers or host names.

## Quick start (macOS)

You need: a Mac, [LM Studio](https://lmstudio.ai) with a model that supports tool calling (a mid-size one such
as Gemma 4 26B works), Python 3.9+, and an SSH alias for the server you want to assess.

```
git clone https://github.com/The-CyberHygiene-Project/Automated_Compliance.git
cd Automated_Compliance
pip3 install pytest && python3 -m pytest -q tests   # the tests need no model and no server
reference/fetch_nist_data.sh                     # NIST's public data files
mkdir docs                                       # a read-only copy of your compliance documents
TARGET=<ssh alias> ./assess.sh --only 3.1.1      # try one Rev 2 requirement
REV=3 TARGET=<ssh alias> ./assess.sh             # the full Rev 3 run (many hours; resumable)
```

Keep the folder outside `~/Desktop` and `~/Documents` (the sandbox blocks those). Keep answer keys in
`~/compliance-private` or point `R2_ANSWER_KEY` and `R3_KEY_DIR` elsewhere. Run in a real Terminal window.

## Limits, stated plainly

- A local model can be lenient: in the first trial it marked some partly-met objectives Met.
- Requirement-level agreement with a key says little about objective-level accuracy.
- Interviews, physical checks and training records cannot be judged from a server and documents; the AI should
  say "Not checkable".
- The Rev 3 key is derived from Rev 2 determinations and is provisional by construction.
- A full run takes many hours on a laptop-class machine.

## Sources and license

NIST's publications and data (SP 800-171, 800-171A, the OSCAL catalog, the Rev 2 to Rev 3 mapping) are U.S.
government works; this repository only reads and reformats them.
Code and documentation: [Apache License 2.0](LICENSE).
