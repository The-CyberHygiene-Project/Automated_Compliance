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
