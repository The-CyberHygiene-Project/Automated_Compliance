# Evidence and record-keeping tools (reference copies)

These are the scripts one small reference system uses to **collect evidence** and to **keep its System Security Plan
(SSP) and Plan of Action and Milestones (POA&M) true**. They are published so another small business can see how the
work is done and adapt it. They are not a product.

> **Read this first.**
> - **Redacted reference copies.** Addresses, the owner, the organization, the domain, the user name and some host
>   names are replaced with placeholders such as `[USERNAME]` and `[LAN-IP-REDACTED]`. A script will not run until you
>   put your own values back.
> - **Not validated.** They run on one system. Nothing here has been tested on another.
> - **Not run during preparation.** Each description below comes from reading the code (marked where only part was
>   read). Read a script before you run it, especially anything marked "needs root".
> - **Passwords in the two negative tests are throwaway.** The test accounts and their test passwords are disposable
>   fixtures; the values in these copies are newly generated, with the same lengths and character mix as the
>   originals so the tests still mean the same thing.
> - **No data files are included**: no assessment, ledger, schedule or evidence notes. Redacted examples of evidence
>   notes are in the `diwai` repository under `CyberSecurity/Evidence/`.

How these fit together is explained in
[How evidence is collected and how the SSP and POA&M are updated](How_evidence_is_collected_and_how_the_SSP_and_POAM_are_updated.md).

## What is here

| Folder | Purpose |
|---|---|
| `record-tools/` | Keep the record true: roll-up counts, freshness and cross-reference checks, citation checks, the recurring-duties ledger |
| `collection/` | Collect or publish evidence: a host evidence run, a health monitor, scan reports and vulnerability scans |
| `collection/legacy-dc1/` | An older collector from a separate production network, kept because the method is reusable |
| `tests-and-drills/` | Negative tests (prove a control refuses what it should), exercises, and post-change checks |

## At a glance

| Script | Needs | Writes | Changes the system? |
|---|---|---|---|
| `record-tools/count.py` | Python 3 | stdout | No |
| `record-tools/assessment-status.py` | Python 3 | stdout | No |
| `record-tools/worklist.py` | Python 3 | its JSON data file, two HTML files | No (edits its own data and pages) |
| `record-tools/doc-freshness.py` | Python 3 | baseline file; `adopt`/`publish` copy files | Copies controlled documents only |
| `record-tools/xref-sweep.py` | Python 3 | stdout | No |
| `record-tools/sweep-citations.py` | Python 3 | stdout | No |
| `record-tools/obligations-log.py` | Python 3 | appends one line to the ledger | Ledger only |
| `record-tools/obligations-sync.py` | Python 3, open ssh login | inserts rows in the ledger | Ledger only |
| `record-tools/obligations-status.py` | Python 3, open ssh login, read-only `sudo -n` on the server | stdout | No |
| `collection/collect-mac-evidence.sh` | **root** | one evidence text file | Stated read-only; see entry |
| `collection/control-health-monitor.sh` | root, on the server | JSON report, state file, syslog, local mail | No (monitor only) |
| `collection/mscp-report.py` | Python 3 | report files | No |
| `collection/publish-mscp-evidence.sh` | Nextcloud `occ` | evidence files, log, re-index | No |
| `collection/scap-report-to-pdf.sh` | Chrome, Nextcloud | PDFs; deletes the staged HTML | No |
| `collection/cve-scan-vm` | network, rights to write under `/var` | cache, report | No |
| `collection/cve-scan-mac` | network, Homebrew | cache, report | No |
| `collection/legacy-dc1/collect_openscap_results.sh` | ssh and `sudo` on remote hosts | reports, summary, web page | **Yes in `--scan-and-collect` mode** |
| `tests-and-drills/negative-test-credential-policy.sh` | **root** (Mac) | nothing kept | **Yes**: creates and deletes a local account |
| `tests-and-drills/negative-test-directory-policy.sh` | **root** (server) | nothing kept | **Yes**: creates and deletes a directory entry |
| `tests-and-drills/correlation-exercise.sh` | ssh, read-only `sudo -n` on the server | stdout | Creates real failed-login events |
| `tests-and-drills/media-sanitization-drill.sh` | macOS `hdiutil` | disposable images, deleted | Disposable files only; see warning |
| `tests-and-drills/post-reboot-check.sh` | normal user | stdout | No |
| `tests-and-drills/post-upgrade-verify.sh` | sudo prompt, ssh | stdout | No |

## One thing to know before you roll up a count

`count.py` and `assessment-status.py` both read the same assessment table, but they **disagree on one word**:
`count.py` treats a requirement as met when every objective is *satisfied or not applicable*;
`assessment-status.py` counts it as met only when every objective is *satisfied* (not applicable does not count).
If a requirement has any not-applicable objective, the two will report different numbers. Decide which rule you mean,
write it down, and use one tool. Both skip a table row whose status is not one of the five known words without
saying so (`count.py` at least prints the requirements for which it found no rows).

## Entries

Each entry says what the script does, what it reads, what it writes, what it changes, how to run it and its limits.
"Read in full" means the whole body was read when this was written.

### record-tools/count.py *(read in full)*
**Does:** parses the self-assessment (four table layouts) and prints, per requirement, whether it is *fully met*: every objective satisfied or not applicable. Prints totals, a per-family pair (requirements, met), and the requirements for which no rows were parsed.
**Reads:** the assessment file you name. **Writes:** nothing but standard output. **Changes:** nothing.
**Run:** `python3 count.py assessment.md`
**Limits:** depends on exact heading and status words; see the note above on not-applicable.

### record-tools/assessment-status.py *(read in full)*
**Does:** computes the family table straight from the assessment, with two measures: requirements met (every objective satisfied) and objectives passing. A range such as `[a]-[c]` counts as three objectives and `[a]/[b]` as two. `--json` prints JSON.
**Reads:** the assessment (a default path is built in; `--file` overrides). **Writes:** standard output. **Changes:** nothing.
**Limits:** the default path is site-specific; status words other than the five known ones are skipped silently; differs from `count.py` on not-applicable.

### record-tools/worklist.py *(header and structure read; render body not read in full)*
**Does:** renders a to-do list held in a JSON file as an HTML page and fragment for a portal; `close REQ "note"`, `reopen REQ`, `status`.
**Reads/writes:** its JSON data file (rewritten on close and reopen) and two HTML files in the portal source folder. **Changes:** nothing on any host.
**Limits:** it tracks the work, not the score; closing an item is a reminder to re-determine the requirement. The data file is site content and is not included.

### record-tools/doc-freshness.py *(read in full)*
**Does:** keeps a baseline (the hash of the canonical copy at the last sync) and labels each tracked working document IN SYNC, LOCAL AHEAD, STALE, DIVERGED, UNKNOWN or LOCAL ONLY. Commands: `status`, `check FILE` (exit 0 means safe to edit), `adopt FILE` (copy canonical over the working copy), `publish FILE` (copy the working copy to canonical; refuses STALE, DIVERGED and UNKNOWN), `accept FILE` (record the baseline without copying). It fails closed: if the canonical store cannot be read it says so and checks nothing.
**Reads:** the canonical folder, the tracked working folders, the baseline file. **Writes:** `status` and `check` write the baseline only to record an IN SYNC document; `adopt` and `publish` copy files; `accept` writes the baseline.
**Limits:** matches files by name (with a small alias table); tracks only `.md` files in the folders it is configured for; proves "has the canonical copy moved", not "is the content right"; after `publish` you must refresh your document store's index yourself (it prints a reminder).

### record-tools/xref-sweep.py *(read in full)*
**Does:** finds live pointers that **resolve but name a superseded version** (file citations like `X_v1.7.md`, and prose like "SSP v2.13"). It deliberately skips dated records, superseded documents, revision-history sections and "Supersedes" lines, because a dated record that cites an older version is correct. Exits 1 if it finds any. It reports; it does not edit.
**Reads:** the canonical folder. **Writes:** standard output.
**Limits:** "current" means the highest version number found; only `_vN.N` file names and "SSP/POA&M/SBOM vN.N" prose are recognised; the rules for "historical" lines are heuristics.

### record-tools/sweep-citations.py *(read in full)*
**Does:** builds an inventory of existing documents, declared document IDs and evidence IDs, then lists citations that do not resolve: missing documents, unresolved document IDs, unresolved evidence IDs. It also lists absolute host paths that documents cite, for manual checking.
**Reads:** the canonical folder, the local assessment folder, and `.md` files in the working root. **Writes:** standard output. **Changes:** nothing.
**Limits:** proves only that a citation points at something that exists, not that it points at the right version (that is `xref-sweep.py`). Host paths are listed, not checked. Folder paths are hard-coded.

### record-tools/obligations-log.py *(read in full)*
**Does:** appends one row (date, obligation ID, outcome, who) to the recurring-obligations ledger. It requires an ID that exists in the schedule and an outcome of at least three words, so "ran" with no finding is refused. `--backfill` marks a late entry.
**Run:** `obligations-log.py ID "what was found" [--by NAME] [--date YYYY-MM-DD] [--backfill]`
**Limits:** no duplicate check; hard-coded ledger and schedule paths; a `|` in the outcome is changed to `/`.

### record-tools/obligations-sync.py *(read in full)*
**Does:** reads the duties log written by the portal's routine-duties page on the server, over ssh (it tries `sudo -n cat` first, then plain `cat`), and inserts entries not already in the ledger.
**Needs:** an open ssh login. **Limits:** an entry is skipped only if the identical line is already present; the ssh user and host alias are hard-coded.

### record-tools/obligations-status.py *(read in full)*
**Does:** an overdue report for the schedule. Manual items: last ledger date against cadence (daily 3 days, weekly 8, monthly 32, quarterly 93, annual 367). Automated items: asks the server over ssh for the last run time and result of named jobs (`systemctl show`, and `sudo -n` for a few log reads), and reads the latest Time Machine backup name locally. Prints OK, OVERDUE or NO EVIDENCE for each item.
**Writes:** nothing. **Limits:** job names and log paths are hard-coded; a failed probe prints "NO EVIDENCE" rather than stopping.

### collection/collect-mac-evidence.sh *(read in full)*
**Does:** a one-time evidence run written for an August 2026 sweep. Run as root, it writes one timestamped text file with: FileVault, System Integrity Protection, Gatekeeper, the pf firewall (state, anchors, rules), the application firewall, one launch service, the Wazuh agent (status, a few config lines, log tail), pending software updates, listening ports, local accounts and the admin group, the password policy, screen-lock settings, audit settings, a TLS certificate, Nextcloud status and its two-factor app state, the size of the weekly scan wrapper (it was once a zero-byte file), and an mSCP compliance audit.
**Changes:** the script states "read-only: inspects and scans, changes nothing". It runs the mSCP audit script with `--check` (audit only; `--fix` is never passed). **What the mSCP audit script itself writes was not confirmed**; mSCP audit scripts normally keep their own results file.
**Run:** `sudo ./collect-mac-evidence.sh` (it exits if not root).
**Limits:** hard-coded to one site's paths, user, service names and certificate; output is trimmed with `head` and `tail`; the mSCP step takes several minutes; macOS updates change command output.

### collection/control-health-monitor.sh *(header and structure read; the individual checks were not each read)*
**Does:** verifies that security controls are *running*, not just configured. Written after four controls were found believed-running but inert (the SIEM down for about 21 hours, an agent offline for 12 days, a weekly scan executing a zero-byte script, a clock 24 minutes adrift while its sync tool reported perfect). Runs on the server; the reference system runs it every 15 minutes from a timer. Each run records about three dozen individual checks (35 in the most recent report seen) grouped in numbered sections (SIEM running, agents connected, audit subsystem, clock, scheduled scans producing output, the encrypted archive pipeline, vulnerability scanning and its data, protective services, SELinux and FIPS enforcing, certificate expiry, an authenticated-path probe, a directory-password check, audit warnings reaching a person, the SIEM API, inactivity enforcement, patch-review cadence, SSH still demanding a one-time code, a document editor answering, a credential register past its dates).
**Writes:** a machine-readable `latest.json`, a state file, syslog lines (so the SIEM sees them), and local mail on a **change of state** or after a set number of hours (earlier it mailed every run, which produced up to 96 identical mails a day). Recovery notices stay local. Alerts go by both syslog and mail because a SIEM-only alert is useless when the SIEM is what failed.
**Needs:** root on the server; reads logs and SIEM alert files. **Changes:** nothing on the controls it checks.
**Limits:** the checks are specific to this system's software and names; the number of checks has grown (another script here still expects the older count of 24); email addresses and secret-looking text are scrubbed from the detail it records. Nobody is told unless someone reads the mail, so it needs a person or a page that reads it.

### collection/mscp-report.py *(header, counting logic and argument handling read; the HTML-building half was not read in full)*
**Does:** turns the mSCP audit result (a property list written by the weekly scan) into a readable report. It counts only entries that are rules with a true/false finding; the file also holds a timestamp key that an earlier dashboard had counted as a passing rule.
**Reads:** the audit plist. **Writes:** report files into `--out` (default: the evidence store's scan folder). **Run:** `mscp-report.py [--out DIR]`
**Limits:** hard-coded plist and default output paths.

### collection/publish-mscp-evidence.sh *(read in full)*
**Does:** publishes the weekly mSCP audit result into the evidence store, dated by the plist's modification time: a markdown summary (pass and fail counts, failing rule names, the plist's SHA-256, the matching scan-log section), a copy of the plist, and a "latest" copy; then re-indexes the document store. It does nothing if that date is already published. It is audit-only: it reads results and never scans or fixes anything. Runs as a normal user.
**Writes:** files in the evidence Scans folder, a log in the user's Library, and runs the document store's `occ groupfolders:scan`.
**Limits:** markdown only (no PDF); paths and a host name in the generated text are fixed; the plist is trusted as found.

### collection/scap-report-to-pdf.sh *(read in full)*
**Does:** converts OpenSCAP HTML reports waiting in a staging folder to PDF with headless Chrome. It forces the hidden "result details" section visible, because otherwise the PDF is a five-page summary with no rule results. It refuses any PDF under 50 pages, files the PDF in the evidence Scans folder (and a "latest" copy for the services report), deletes the staged HTML only after the copy succeeds, and re-indexes.
**Needs:** Google Chrome and Nextcloud on the same Mac. **Limits:** the page-count test is a heuristic; the Nextcloud user name and paths are fixed.

### collection/cve-scan-vm *(header and structure read; the scoring logic was not read in full)*
**Does:** a vulnerability check for a Rocky Linux server, written because configuration scanning does not say whether installed packages have known flaws, and the distribution's own update metadata was empty. It downloads Rocky's errata, compares each fixed package version with the installed one using rpm's own version comparison, and reports older ones. Exit codes: 0 none, 1 moderate or low only, 2 important or critical, 3 error.
**Network:** fetches `errata.rockylinux.org` (cached for 2 days; the scan reports the cache's age). **Writes:** a cache under `/var/lib/oval`, a report under `/var/log/oval`, and optional JSON (`--json PATH`). **Changes:** no packages.
**Limits:** Rocky-specific; the cache location needs write access under `/var`.

### collection/cve-scan-mac *(header and structure read; the scoring logic was not read in full)*
**Does:** a less precise vulnerability check for a Mac. It states its own limits: Homebrew results come from NVD CPE matching on the formula name (a guess, so a formula whose name differs returns nothing, a false negative it cannot detect); NVD says which versions are affected, not whether Homebrew has since patched; Python packages come from OSV.dev; macOS itself is only "updates pending or not". Results are advisory. Exit codes: 0 clean, 1 findings none critical, 2 critical or high, 3 error.
**Network:** NVD (paced to its limit) and OSV.dev. **Writes:** a cache in the user's Library/Caches, logs, and a dated JSON report in a reports folder. A suppression file can silence findings with reasons. **Limits:** absence of a finding is not evidence of safety.

### collection/legacy-dc1/collect_openscap_results.sh *(header, configuration, helper functions and the collect section read; the parsing and HTML-dashboard sections were not read in full)*
**Does:** from a central server, fetches the latest OpenSCAP HTML and XML results from itself and three workstations (over ssh, using `sudo cat` on the remote file), then writes a markdown summary and an HTML dashboard for the server's internal web page.
**Modes:** `--collect-only` (default) fetches existing results. **`--scan-and-collect` runs `sudo` on the workstations to start new scans first, so it is not read-only.**
**Origin:** a separate production network's script (workstation names are replaced with `ws-a`, `ws-b`, `ws-c`). Kept because the collect-then-summarise method carries over.
**Limits:** hard-coded host names, key path and output folders.

### tests-and-drills/negative-test-credential-policy.sh *(read in full)*
**Does:** proves a Mac's account policy *refuses* what it should, using a disposable standard account: (1) a 6-character and a 15-character password are rejected against a 16-character minimum; (2) reusing the previous password is rejected; (3) after 7 wrong passwords the correct one is also rejected (lockout after 5). Every test expects a failure; one that succeeds where it should fail is reported FAIL; one that could not run is INCONCLUSIVE. The account is removed on exit (including on error), and if removal fails the script prints the command to do it by hand.
**Needs:** root. **Changes:** creates and deletes a local account; the attempts are real authentication failures and will appear in your SIEM.
**Limits:** assumes the policy values in its comments (16 characters, 6 generations, lockout at 5); written for one macOS release's `dscl` and `pwpolicy` behaviour.

### tests-and-drills/negative-test-directory-policy.sh *(read in full)*
**Does:** the same idea for a directory server (389-DS): a disposable inetOrgPerson entry (no login rights) is created over the local socket, then each test runs *as that user* over verified LDAPS: minimum length (6 and 15 refused, 16 accepted), password history (a refusal counts only if the message names history) and lockout (4 wrong binds, then the correct one is refused with a lock-related message). A refusal for the wrong reason is INCONCLUSIVE, not PASS.
**Needs:** root on the server (the header shows how the reference system runs it over ssh with a one-time sudo prime). **Changes:** creates and deletes the test entry and changes its password; failed binds appear in the SIEM.
**Limits:** assumes minimum length 16, history 6 and lockout after 3 failures; the test passwords are throwaway values.

### tests-and-drills/correlation-exercise.sh *(read in full)*
**Does:** a requirement 3.3.5 exercise: three failed ssh logins as a user that does not exist, from the Mac to the server, then after a short wait it reads the server's sshd journal, audit log and SIEM alerts for that user so one event can be traced across sources by time, user and address. Source 4 is only a printed note.
**Needs:** ssh and the read-only `sudo -n` exceptions on the server. **Changes:** nothing, other than generating real failed-login events and alerts.

### tests-and-drills/media-sanitization-drill.sh *(read in full)*
**Does:** a requirement 3.8.3 drill on **disposable disk images only**: an unencrypted 8 MB image is overwritten and a marker string is searched for before (a positive control) and after; an encrypted 8 MB image is made with a random key, mounted with it, then the key is discarded and mounting without it is shown to be refused. Everything is cleaned up.
**Warning:** the working folder is the first argument (default `/tmp/diwai-sanitize-drill`) and the script runs `rm -rf` on it at the start and the end. **Never pass it a real folder.**
**Limits:** it shows the method works on images; it does not sanitize or prove anything about real media.

### tests-and-drills/post-reboot-check.sh *(read in full)*
**Does:** read-only checks after a Mac restart: an app version unchanged, the local model server lists its models, listeners are on loopback only and retired ports are silent, named launch agents are loaded, a web app's health answers, the document-library server answers with a document count, and the server's web service returns an expected code. Exit status is the number of failed checks.
**Limits:** hard-coded to one stack (versions, ports, model names).

### tests-and-drills/post-upgrade-verify.sh *(read in full)*
**Does:** checks after an operating-system and kernel upgrade: the Mac version changed, FileVault on, firewall rules intact (it asks for `sudo` to read them and says "not verified" if it cannot), Wi-Fi off, services running, HTTP checks, the server reachable over ssh, the new kernel running, eleven services active, and the monitor's result.
**Limits:** it contains version numbers from one upgrade (macOS and kernel) and expects the monitor's old "24 checks" wording, so it needs editing for any other use. It does not change configuration.

## Not included, and why
- Live data: the assessment, ledger, schedule, worklist data, evidence notes, change records. See the `diwai` repository for redacted examples.
- The portal and its endpoints (they hold site links and results).
- Any script I could not find. A legacy script that once held a plaintext NAS password was **not found** in the places searched, so nothing is published for it.
