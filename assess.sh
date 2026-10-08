#!/bin/bash
# Run the local-AI 800-171A assessment, one requirement per round. Run it in a real Terminal window.
#
#   TARGET=<ssh alias of the server> ./assess.sh                    Rev 2 kit (320 objectives)
#   REV=3 TARGET=<alias> ./assess.sh                                Rev 3 kit (510 objectives)
#   MODEL=<LM Studio model id> TARGET=<alias> ./assess.sh           another model
#   RUN=2 TARGET=<alias> ./assess.sh                                also allow the optional library search (port 8767)
#   ./assess.sh --only 3.1.1,3.1.2                                  only some requirements
#   ORG_PROFILE=profile.ini REV=3 TARGET=<alias> ./assess.sh        also tell the assessor the facts you stated (see README)
#   TAG=<word> ...                                                  write to a new results folder (never skips an earlier run)
#   STRICT=1 REV=3 ... --only <ids>                                 calibration: a policy proves "defined", not "implemented"
#   ./assess.sh --ask                                               ask a person about unlisted commands
#                                                                   (default: they are declined, nobody needs to watch)
# A stopped run resumes where it left off. Results: results/<run>/ (assessment.md, grade.md, log.jsonl).
# Keep this folder OUTSIDE ~/Desktop and ~/Documents (the sandbox blocks those). Keep your answer keys in
# ~/compliance-private (also blocked from the AI).
ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$ROOT" || exit 1
export TARGET="${TARGET:?set TARGET to the ssh alias of the server to assess}"
MODEL="${MODEL:-google/gemma-4-26b-a4b-qat}"; RUN="${RUN:-1}"; REV="${REV:-2}"
LMS="${LMS:-$HOME/.lmstudio/bin/lms}"
PROFILE="$ROOT/.sandbox.generated.sb"
sed "s|__HOME__|$HOME|g" sandbox.sb > "$PROFILE"
[ "$RUN" = 2 ] && echo '(allow network-outbound (remote ip "localhost:8767"))' >> "$PROFILE"
export SOCK="$ROOT/.target.sock"
echo "Connecting to $TARGET (log in as usual if asked)..."
ssh -S "$SOCK" -O check "$TARGET" 2>/dev/null || ssh -MNf -o ControlPersist=12h -S "$SOCK" "$TARGET" || exit 1
echo "Loading $MODEL..."
"$LMS" unload --all >/dev/null 2>&1
"$LMS" load "$MODEL" --context-length 65536 -y >/dev/null || exit 1
KITARG=(); SUF=""; [ "$REV" = 3 ] && KITARG=(--kit kit-r3/objectives.md) && SUF="-r3"
# ORG_PROFILE: the context is built HERE, outside the sandbox. The AI never reads the profile, only this short file.
CTXARG=()
if [ -n "$ORG_PROFILE" ]; then
  python3 org_profile.py --context "$ORG_PROFILE" > "$ROOT/.context.json" || { echo "The profile has errors above; fix them and run again."; exit 1; }
  CTXARG=(--context .context.json)
fi
STRICTARG=(); [ -n "$STRICT" ] && STRICTARG=(--strict) && SUF="$SUF-strict"
NAME="run$RUN$SUF-${MODEL##*/}"
[ -n "$TAG" ] && NAME="$NAME-$TAG"
ASK=--no-ask; ARGS=(); for a in "$@"; do [ "$a" = --ask ] && ASK= || ARGS+=("$a"); done
sandbox-exec -f "$PROFILE" /usr/bin/python3 assess.py --model "$MODEL" --run "$RUN" --name "$NAME" "${KITARG[@]}" "${STRICTARG[@]}" "${CTXARG[@]}" $ASK "${ARGS[@]}"
OUT="results/$NAME"
if [ "$REV" = 3 ]; then python3 grade_r3.py "$OUT/assessment.md" "$MODEL (run $RUN, Rev 3)" > "$OUT/grade.md"
else python3 grade.py "$OUT/assessment.md" "$MODEL (run $RUN)" > "$OUT/grade.md"; fi
echo "Done: $OUT/assessment.md and $OUT/grade.md"
# Rev 3: also write the results into a copy of the measurement register (never overwrites an existing file)
# WORKING_REGISTER=<your edited register> merges the new scan into it (your edits are kept; the file is not touched).
if [ "$REV" = 3 ] && [ -z "$STRICT" ]; then      # a calibration run never writes a register
  if [ -n "$WORKING_REGISTER" ]; then python3 fill_register.py "$OUT" --into "$WORKING_REGISTER" --out "$OUT/register-merged-$(date +%F).xlsx" || echo "(not merged; see the message above)"
  else python3 fill_register.py "$OUT" --out "$OUT/register-filled-$(date +%F).xlsx" || echo "(register not written; see the message above)"; fi
fi
