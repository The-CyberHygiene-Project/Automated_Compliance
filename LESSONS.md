# Lessons learned

What went wrong, what it cost, and the fix. Written for anyone repeating this kind of test.

1. **A chat-style coding assistant is the wrong shell for this.** In its default "whole file" mode, every code
   block the model writes becomes the contents of the results file, so commands never ran. In "diff" mode they
   ran, but one long conversation filled a 64K-token memory after a single large document. A runner with
   tools and a fresh memory per requirement fixed both.
2. **One big conversation cannot cover 300-plus objectives.** Work per requirement; trim old tool output;
   scale the step limit with the number of objectives; in the last steps offer only the recording tool.
3. **Some chat templates reject a user message that follows a tool result.** The server answered HTTP 400.
   Attach runner reminders to the last tool result instead.
4. **A list of safe commands needs real parsing.** Splitting like a shell, refusing operators and substitution,
   re-quoting, and treating "can change something" forms (`sysctl -w`, `find -exec`) as unlisted caught cases a
   word list would miss. Refuse by file name patterns too (`*_key`, `pin.txt`, shadow files).
5. **Check the kit, not just the model.** A copy of the objective list was missing the 23 requirements that
   NIST numbers without a letter (for example 3.13.4): 297 lettered plus 23 single is 320. Rev 3's 422
   objectives omit the 88 parameter objectives; a second source built from the same catalog confirmed counts
   and wording and showed that naming the parameter each objective depends on helps.
6. **A parameter is not a control.** The AI should mark a parameter objective Met only when a document states
   the value, and quote it. The ones it cannot find are the most useful output.
7. **Tables hold the current value; notes hold history.** The first Rev 2 grader nearly applied superseded
   determinations as current. Read the table, report the note.
8. **A derived key is not ground truth.** Say so in every row, and keep it where the AI cannot read it.
9. **Models differ more in tool use than in knowledge.** One mid-size model looped, repeating the same reply;
   another planned requirement by requirement and recorded complete answers. Test the model in the harness.
10. **The AI can be too kind.** In the first trial it marked partly-met objectives Met and overstated whether
    its evidence came from the server or from documents. Grading against a human key, with every disagreement
    reviewed, is the safeguard.
11. **Tell the person when they are needed.** An approval prompt that nobody sees stalls a run for hours.
    Default to unattended with a fixed list, and speak an alert when a person is required.
12. **Treat documents and command output as data, never instructions.** The rules say so, and the sandbox and
    command list hold even if the model is talked into something.
13. **A control believed to be running may be inert.** Four controls were reported working that were not. A
   monitor that checks each control by effect (not by "the service is up") found them. Check the effect.
14. **A parser that skips what it cannot read hides failures.** A status cell with extra text was silently dropped
   and a requirement counted as unmet. The fix is a report of requirements with no rows, printed every run.
15. **Do not test with a real account name.** Probe logins with a real user's name counted as that user's failed
   attempts and locked the real account. Use made-up names and read the server's own result code (not the
   application's error text).
16. **Stored secrets can carry an invisible newline.** A password stored from a file with a trailing newline did not
   match the same password typed or read stripped; services failed to log in for two minutes. Store and compare the
   exact bytes.
17. **A change check can be wrong, not just the change.** A verification step that cut output short made a good
   change look failed, and the automatic undo reverted it. Safe, but verify the check itself on a known-good case.
18. **Judge a syntax check by exit status.** A benign warning in the checker's text made a good firewall change
   look broken. Use the exit code and show the text.
19. **Every access-path change needs an automatic undo.** Firewall, remote-login and authentication changes ran with
   a timed revert that restores the old state unless confirmed. Several saved a lockout.
20. **Test the alert, not the command.** A notification script was started for hours with a missing argument, printed
   its usage text, and never sounded. Confirm the owner actually sees or hears it once.
21. **Time-based fixes need a verify date.** A retention setting only proves itself when the oldest file reaches the
   limit. Put that date in the schedule when you make the change.
22. **Collect observations before blocking.** For a firewall allow-list, log inbound traffic for a day or more first,
    then write the list from what was seen.
23. **A person who leaves, or a device that goes, needs an end-to-end drill.** Create a disposable account, remove it
    through the written steps, and show every door refuses it. This found a gap (a long-lived application password
    outliving the account).
24. **One source for each document, and an editor that does not rewrite it.** See "Documents live in one place".
25. **Inventories turn "probably" into "yes".** Writing down every external system and every authorised device made
    the open questions visible (what is sent to each, how a new device would be noticed).
26. **A search tool for a small local model must not demand an exact phrase.** A read-only file search that
    matched only the whole phrase returned nothing for natural queries, and the model rephrased and retried until
    it looked like a loop. It was not a context limit. Matching files that contain all the words, in any order, and
    saying plainly "do not repeat this search; try one distinctive word or search by file name" ended it.
27. **A system used in bursts will show gaps; the test is recovery.** After several idle days, two scheduled-job
    checks went red together. Both traced to one planned maintenance window and cleared on the next scheduled run.
    Judge a monitor on whether it notices a gap and the jobs recover, and record the window as planned, not as an
    incident.
