# Method

## The rule of the test

**The AI does the scanning and the judging, unaided.** The tools around it only stage inputs, enforce limits and
check the shape of the record. A person approves the command list in advance, once, and any change to the
list needs a new review.

## One round

For each requirement the runner starts a new conversation containing:

- the rules (statuses, evidence expectations, what the tools do);
- the requirement and its objectives;
- short notes the model saved in earlier rounds.

The model may call these tools:

| Tool | What it does |
|---|---|
| `run_on_server` | One read-only command on the server, checked against the approved list first |
| `list_documents`, `search_documents`, `read_document` | Read the organization's documents (a read-only copy in `docs/`) |
| `search_library` | Optional: search a local document library (run 2) |
| `save_note` | Keep a short note for later rounds |
| `record_results` | The answer: one entry per objective with status, source and evidence |

Safety nets that proved necessary: a memory budget (old tool output is trimmed); one extra step for every
objective beyond six; in the last two steps only `record_results` is offered; a repeated command is not run twice;
reminders ride on the last tool result (some chat templates reject a user message after a tool message).

## The command list

`allowlist.py` returns one of three verdicts for a command:

- **auto**: a read-only form of a listed command (for example `systemctl status`, never `restart`);
- **refuse**: reads a secret (shadow files, private keys, stored credentials, searches for passwords);
- **ask**: everything else, including pipes, redirects, `;`, `&&`, `$(...)`, `sudo` without `-n`.

The command is split as a shell would, then re-quoted before it is sent, so the server's shell cannot read an
argument as an operator. The tests list what runs, what is refused and what asks.

## Statuses

Met, Unmet, N/A, Not checkable. "Not checkable" is a legitimate answer: it means neither the server nor the
documents can show it, and the AI says what evidence would be needed.

## Answer keys

**Rev 2.** The organization's own objective-level self-assessment. The grader reads its tables (the current
determination); notes that record superseded determinations are history, not values.

**Rev 3.** No organization has Rev 3 determinations yet, so `key_r3.py` derives a *provisional* key:

- NIST publishes a Rev 2 to Rev 3 mapping. Each Rev 3 requirement takes the aggregated Rev 2 determination of
  the requirement(s) it came from, including withdrawn requirements folded into it.
- Basis **carried**: Rev 3 changed little; the Rev 2 result is the expected result.
- Basis **ceiling**: significant change or new parameters; the Rev 2 result is a best case.
- Basis **new**: no Rev 2 counterpart; no key, listed for a human.
- It is requirement-level (NIST gives no objective-level mapping) and parameter objectives have no key.
- Every row says it is derived, not independent, and that a human must confirm it.

The grader reports where the AI is more lenient or stricter than the key, and lists every parameter for which
no document states a value.

## Keeping the AI away from the answers

The sandbox profile denies the AI read access to the key folder, notes, `~/Desktop`, `~/Documents` and other
volumes, and limits the network to the local model server and the one SSH socket. The documents it assesses
are a copy that leaves out the self-assessment.
