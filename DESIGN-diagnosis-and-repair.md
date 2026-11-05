# Design note: diagnosis and repair (draft for comment)

**Status:** a design with a first slice under way on one reference system. The first slice is tier 1 only (read-only facts), a mapping from a monitor's failing checks to plain-language cards, and tests with planted failures. Tiers 2 and 3, the model comparison and any display page are not built. Nothing here has been validated. The assessor and its read-only allow-list are unchanged.

## Why

Knowing that a control has failed is the first step. The next steps are to gather facts about the failure, diagnose it, and decide what to do. If the network is impaired, a local model on one machine is the line of defence, so these steps must work from a terminal on that machine and must not depend on a web page or a cloud service.

This note extends the project's discipline (a local model, a human in control, nothing unattended that could do harm) from assessing to diagnosing and, later, repairing. It builds on [`DESIGN-remediation-triage.md`](DESIGN-remediation-triage.md), whose steps 3 and 4 it takes over.

## Principles

1. **The model chooses; code executes.** The model never writes a shell string. It names an entry in a catalog and supplies parameters. Code checks them and runs the entry's fixed command without a shell, with a time limit and an output limit.
2. **A catalog is the only way a command runs.** A command that is not in the catalog cannot run. Each entry has a fixed program, parameters limited to a list of choices or a checked pattern, a host, and a risk tier. The person who owns the system approves the catalog; any edit to it withdraws that approval until it is approved again.
3. **Risk tiers, set by the catalog, never by the model.**

   | Tier | What it is | Who approves a run |
   |---|---|---|
   | 1 | Read-only diagnostics: service state, log reads, file ages, certificate dates. No writes, no elevated rights, no network fetches. | No one per run (the entry itself is approved once); a step limit applies per case. |
   | 2 | Tests that touch something but are safe and undoable: a synthetic probe, a dry run. | A person, every run. |
   | 3 | Anything that could damage the system or irreversibly change a configuration file or similar, and every fix step. | A person, every run, with a hardware-key signature, after a backup, with verify and undo defined. |

   An entry with no tier, or an unclear effect, is tier 3. A test checks every tier 1 entry for write, delete, rename, restart, elevated-rights and network-fetch calls.
4. **Untrusted text is data.** Log lines and command output can contain text written by an attacker. It is cleaned of control characters, escaped, and placed inside a marked data block. The session that reads untrusted text holds no tier 2 or 3 tool; those run only through the approval path, outside that session.
5. **The diagnosing model never judges its own repair.** A repair is verified by the same read-only check that failed, run by code, after a person approved the repair.
6. **A diagnosis can name a repair only from an approved list.** Code discards anything else the model suggests.
7. **Honest gaps.** A failing check with no card is reported as a gap, with whatever facts were gathered. It is never dropped.

## How a diagnosis runs

1. The monitor's report is read (read-only). A stale or unreadable report is itself a finding.
2. For each failing check, code gathers facts by running that check's tier 1 catalog entries.
3. Optionally, the model may ask for a few more tier 1 entries, one at a time, up to a small step limit. A repeat is refused. Every request, its reason and its result are recorded.
4. The model explains the failure in plain words and may name one repair from the approved list. The case file records exactly what the model saw and said.
5. A person reads the plain-language card and decides. Tier 2 and 3 steps wait for that person.

## Relationship to the rest of the repository

The assessor stays read-only and its allow-list is unchanged. This loop starts from a monitor's failing checks, not from an assessment, and is optional. The repository's principle "lead, don't apply" still holds for the assessor and the triage tool: applying a change happens only through a repair that a person approved, outside the assessor.

## Limits, stated plainly

- A model can be steered by text in logs. The catalog and the approvals limit what that can cause; they cannot make a diagnosis correct. Expect misleading but harmless diagnoses before expecting harmful commands.
- The first score of a local model on this job has not been measured. Do not choose a model, or turn on model-chosen commands by default, before it is.
- Approval of the catalog is a recorded hash, which shows the file is unchanged since a person approved it. It is not a hardware-key signature; tiers 2 and 3 will need something stronger.
- Facts that need elevated rights are not gathered; the case says so.
- Everything here assumes one operator who owns the system. It is not a design for shared administration.
