#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# NEGATIVE TESTS for POA&M-013 (3.1.8 lockout, 3.5.8 reuse) and POA&M-016 (3.5.7
# minimum length) on the Mac host — DIWAI-VS-002 §4 limit 1.
#
# WHY: VS-002 confirmed the diwai.* account policies are PRESENT and well-formed,
# but recorded that none was negatively tested. "Configured correctly" is not
# "enforcement demonstrated" — the exact distinction DIWAI-VS-001 exists to draw.
# A policy that is present but unenforced looks identical from a config dump.
#
# METHOD: a disposable local account. Every test asserts a FAILURE that the policy
# is supposed to cause. A test that SUCCEEDS where it should fail = control not
# enforced. The account is standard (no admin, no SecureToken) and is deleted on
# exit via trap, including on error or interrupt.
#
# Run:  sudo /Users/[USERNAME]/diwai/scripts/negative-test-credential-policy.sh
set -u

U=jdoetest
FULL="John Doe (disposable policy test)"
GOOD1='Fp5&tVp7Gp5^Cy7Nd'     # 17 chars, meets the 16-char minimum
GOOD2='Dm7#pFj7Lf3^Uh2Xb'     # 17 chars, different
SHORT='Uz7%jE'                # 6 chars — MUST be rejected by diwai.minimum.length
FIFTEEN='Rr5@gKf7Jv5^rKa'     # 15 chars, 4 classes — MUST be rejected: the boundary is 16
PASS=0; FAIL=0; INCONCLUSIVE=0

rule(){ printf '%s\n' "--------------------------------------------------------"; }
ok(){   printf '  RESULT: PASS  — %s\n' "$1"; PASS=$((PASS+1)); }
bad(){  printf '  RESULT: FAIL  — %s\n' "$1"; FAIL=$((FAIL+1)); }
huh(){  printf '  RESULT: INCONCLUSIVE — %s\n' "$1"; INCONCLUSIVE=$((INCONCLUSIVE+1)); }

[ "$(id -u)" -eq 0 ] || { echo "must run as root: sudo $0" >&2; exit 1; }

cleanup() {
    rule; printf '  CLEANUP\n'; rule
    if dscl . -read /Users/$U >/dev/null 2>&1; then
        sysadminctl -deleteUser $U >/dev/null 2>&1
        sleep 1
        if dscl . -read /Users/$U >/dev/null 2>&1; then
            dscl . -delete /Users/$U >/dev/null 2>&1
        fi
    fi
    if dscl . -read /Users/$U >/dev/null 2>&1; then
        printf '  WARNING: account %s STILL EXISTS — remove it manually:\n' "$U"
        printf '      sudo sysadminctl -deleteUser %s\n' "$U"
    else
        printf '  account %s removed\n' "$U"
    fi
    [ -d "/Users/$U" ] && rm -rf "/Users/$U" 2>/dev/null
    pwpolicy -u $U -clearaccountpolicies >/dev/null 2>&1
}
trap cleanup EXIT INT TERM

rule; printf '  SETUP — creating disposable account %s\n' "$U"; rule
if dscl . -read /Users/$U >/dev/null 2>&1; then
    echo "  ERROR: $U already exists. Remove it first."; exit 1
fi
sysadminctl -addUser $U -fullName "$FULL" -password "$GOOD1" >/dev/null 2>&1
sleep 2
if ! dscl . -read /Users/$U >/dev/null 2>&1; then
    echo "  ERROR: could not create $U — cannot test."; exit 1
fi
printf '  created (standard user, no admin, no SecureToken)\n'
printf '  baseline auth check: '
if dscl . -authonly $U "$GOOD1" >/dev/null 2>&1; then
    printf 'OK — the account authenticates with its initial password\n'
else
    printf 'FAILED — account will not authenticate; tests below are unreliable\n'
fi

rule; printf '  TEST 1 of 3 — 3.5.7 MINIMUM LENGTH (POA&M-016)\n'; rule
printf '  Attempting to set a %s-character password. Policy requires 16.\n' "${#SHORT}"
printf '  A control that is ENFORCED must REJECT this.\n\n'
if dscl . -passwd /Users/$U "$GOOD1" "$SHORT" >/dev/null 2>&1; then
    bad "the short password was ACCEPTED — minimum length is NOT enforced"
    dscl . -passwd /Users/$U "$SHORT" "$GOOD1" >/dev/null 2>&1   # restore
else
    ok "short password rejected — 16-character minimum is enforced"
fi
printf '  Now a %s-character password (the boundary): it must also be rejected.\n' "${#FIFTEEN}"
if dscl . -passwd /Users/$U "$GOOD1" "$FIFTEEN" >/dev/null 2>&1; then
    bad "the 15-character password was ACCEPTED — the minimum is below 16"
    dscl . -passwd /Users/$U "$FIFTEEN" "$GOOD1" >/dev/null 2>&1   # restore
else
    ok "15-character password rejected — the boundary is 16"
fi

rule; printf '  TEST 2 of 3 — 3.5.8 PASSWORD REUSE (POA&M-013)\n'; rule
printf '  Changing to a new password, then attempting to change BACK.\n'
printf '  Policy keeps 6 generations. An ENFORCED control must REJECT the reuse.\n\n'
if dscl . -passwd /Users/$U "$GOOD1" "$GOOD2" >/dev/null 2>&1; then
    if dscl . -passwd /Users/$U "$GOOD2" "$GOOD1" >/dev/null 2>&1; then
        bad "the previous password was ACCEPTED again — history is NOT enforced"
    else
        ok "reuse of the previous password rejected — history is enforced"
        dscl . -passwd /Users/$U "$GOOD2" "$GOOD1" >/dev/null 2>&1
    fi
else
    huh "could not set the second password, so reuse could not be tested"
fi

rule; printf '  TEST 3 of 3 — 3.1.8 ACCOUNT LOCKOUT (POA&M-013)\n'; rule
printf '  Policy: lock after 5 consecutive failures, auto-release after 900 s.\n'
printf '  Submitting 7 wrong passwords (more than 5, fewer than the old limit of 10), then ONE CORRECT one.\n'
printf '  If enforced, the correct password must ALSO fail while locked.\n\n'
for i in $(seq 1 7); do
    dscl . -authonly $U "definitely-the-wrong-password-$i" >/dev/null 2>&1
done
printf '  7 failed attempts submitted. failedLoginCount now: %s\n' \
    "$(dscl . -read /Users/$U accountPolicyData 2>/dev/null | grep -A1 failedLoginCount | tail -1 | tr -d ' \t' | sed 's/<[^>]*>//g')"
printf '  now authenticating with the CORRECT password...\n'
if dscl . -authonly $U "$GOOD1" >/dev/null 2>&1; then
    bad "correct password ACCEPTED after 7 failures — lockout is NOT enforced"
else
    ok "correct password rejected while locked — lockout is enforced"
fi

rule; printf '  SUMMARY\n'; rule
printf '  PASS %s   FAIL %s   INCONCLUSIVE %s\n\n' "$PASS" "$FAIL" "$INCONCLUSIVE"
if [ "$FAIL" -eq 0 ] && [ "$INCONCLUSIVE" -eq 0 ]; then
    printf '  All three controls demonstrated BY NEGATIVE TEST.\n'
    printf '  DIWAI-VS-002 §4 limit 1 can be closed.\n'
else
    printf '  Not all controls were demonstrated. Show Claude this output.\n'
fi
printf '\n  NOTE: these attempts are real auth failures and WILL appear in the\n'
printf '  Wazuh alert stream. That is expected, and is itself a detection check.\n'
