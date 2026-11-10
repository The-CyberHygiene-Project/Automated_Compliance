#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# NEGATIVE TESTS for the VM directory (389-DS, instance "diwai") — the directory half of
# POA&M-013 (3.5.8 history, 3.1.8 lockout), plus an OBSERVATIONAL 3.5.7 length test.
#
# WHY: 389-DS cn=config shows passwordHistory on / passwordInHistory 6 and
# passwordLockout on / passwordMaxFailure 3. That is configuration, not enforcement.
# The Mac half carried a rule that was listed but silently skipped for five weeks
# (DIWAI-CR-2026-09-03). This proves or disproves the directory half by refusal.
#
# METHOD: a disposable inetOrgPerson entry (NO posixAccount — cannot log in to the VM).
# Created and deleted as root over ldapi (EXTERNAL). Every test runs AS THE USER over
# verified LDAPS — the path the policy governs, not an admin reset. Each rejection must
# carry the RIGHT reason, or it is INCONCLUSIVE rather than PASS.
#
# Run on the VM as root (VM sudo asks for the password since DIWAI-CR-2026-10-06):
#   ssh -tt services 'sudo -v'          (type the VM password once; kept 2 minutes)
#   ssh services 'sudo -n bash -s' < negative-test-directory-policy.sh
#   ssh services 'sudo -K'               (forget it)
set -u
export LDAPTLS_REQCERT=demand

DN='uid=jdoetest,ou=people,dc=diwai,dc=org'
LDAPI='ldapi://%2frun%2fslapd-diwai.socket'
H='ldaps://services.[DOMAIN.ORG]:636'
P1='Ng8&kQq4Lf7^Xy9Ju'
P2='Hw4!yUm6Vz9^Av8Ug'
P3='Wu4#nQp8Sr4#Rk8Hg'
P13='Vj6%eTs3Rh4%rMq'         # 15 chars, 4 categories — must be refused
P14='Pr3^gPr9Ng5@tMhT'        # 16 chars, 4 categories — must be accepted
SHORT='Hq3%wM'
PASS=0; FAIL=0; INCONCLUSIVE=0

rule(){ printf '%s\n' "--------------------------------------------------------"; }
ok(){   printf '  RESULT: PASS  — %s\n' "$1"; PASS=$((PASS+1)); }
bad(){  printf '  RESULT: FAIL  — %s\n' "$1"; FAIL=$((FAIL+1)); }
huh(){  printf '  RESULT: INCONCLUSIVE — %s\n' "$1"; INCONCLUSIVE=$((INCONCLUSIVE+1)); }
exists(){ ldapsearch -LLL -Y EXTERNAL -H "$LDAPI" -b "$DN" -s base dn 2>/dev/null | grep -q '^dn:'; }
# LDAP modify as the user, not the password-modify extended op: the extop returns only a
# generic "Failed to update password", while modify returns the reason (e.g. "password in
# history"). Run 1 of this test came back INCONCLUSIVE for exactly that reason.
change(){ ldapmodify -x -H "$H" -D "$DN" -w "$1" 2>&1 <<EOF
dn: $DN
changetype: modify
replace: userPassword
userPassword: $2
EOF
}
bindas(){ ldapwhoami -x -H "$H" -D "$DN" -w "$1" 2>&1; }

[ "$(id -u)" -eq 0 ] || { echo "must run as root" >&2; exit 1; }

cleanup() {
    rule; printf '  CLEANUP\n'; rule
    exists && ldapdelete -Y EXTERNAL -H "$LDAPI" "$DN" >/dev/null 2>&1
    if exists; then
        printf '  WARNING: %s STILL EXISTS — remove it manually\n' "$DN"
    else
        printf '  entry jdoetest removed\n'
    fi
}
trap cleanup EXIT INT TERM

rule; printf '  SETUP — creating disposable directory entry jdoetest\n'; rule
if exists; then echo "  ERROR: entry already exists. Remove it first."; trap - EXIT; exit 1; fi
ldapadd -Y EXTERNAL -H "$LDAPI" >/dev/null 2>&1 <<EOF
dn: $DN
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: jdoetest
cn: John Doe (disposable policy test)
sn: Doe
userPassword: $P1
EOF
exists || { echo "  ERROR: could not create entry — cannot test."; exit 1; }
printf '  created (inetOrgPerson only — no posixAccount, no group membership)\n'
out=$(bindas "$P1"); rc=$?
if [ $rc -eq 0 ]; then
    printf '  baseline bind over verified LDAPS: OK\n'
else
    printf '  baseline bind FAILED (rc=%s): %s\n  tests below cannot be trusted — stopping\n' "$rc" "$out"
    exit 1
fi
CUR="$P1"

rule; printf '  TEST 1 of 3 — 3.5.7 MINIMUM LENGTH\n'; rule
printf '  cn=config: passwordCheckSyntax on, passwordMinLength 16 (set 2026-10-09, CR-2026-10-11).\n'
printf '  A 6-character and a 15-character password must be refused; 16 must be accepted.\n\n'
out=$(change "$CUR" "$SHORT"); rc=$?
if [ $rc -eq 0 ]; then
    bad "the 6-character password was ACCEPTED — directory minimum length is NOT enforced"
    CUR="$SHORT"
else
    ok "6-character password rejected: $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
fi
out=$(change "$CUR" "$P13"); rc=$?
if [ $rc -eq 0 ]; then
    bad "the 15-character password was ACCEPTED — the minimum is below 16"
    CUR="$P13"
else
    ok "15-character password rejected — the boundary is 16"
fi
out=$(change "$CUR" "$P14"); rc=$?
if [ $rc -eq 0 ]; then
    ok "16-character password accepted — the rule does not over-reject"
    CUR="$P14"
else
    huh "16-character password REFUSED (rc=$rc): $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
fi

rule; printf '  TEST 2 of 3 — 3.5.8 PASSWORD REUSE (POA&M-013, directory half)\n'; rule
printf '  Two legitimate user changes, then reuse of a password THE USER set.\n'
printf '  PASS only if the rejection names history.\n\n'
out=$(change "$CUR" "$P2"); rc=$?
if [ $rc -ne 0 ]; then
    huh "control change to a new password failed (rc=$rc): $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
else
    CUR="$P2"
    out=$(change "$CUR" "$P3"); rc=$?
    if [ $rc -ne 0 ]; then
        huh "second control change failed (rc=$rc): $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
    else
        CUR="$P3"
        printf '  control changes succeeded — the test can discriminate\n'
        out=$(change "$CUR" "$P2"); rc=$?
        if [ $rc -eq 0 ]; then
            bad "a previous password was ACCEPTED again — directory history is NOT enforced"
            CUR="$P2"
        elif echo "$out" | grep -qi 'history'; then
            ok "reuse rejected for history: $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
        else
            huh "reuse rejected, but NOT for history (rc=$rc): $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
        fi
    fi
fi

rule; printf '  TEST 3 of 3 — 3.1.8 ACCOUNT LOCKOUT (POA&M-013, directory half)\n'; rule
printf '  cn=config: passwordMaxFailure 3, lockout 3600 s.\n'
printf '  Submitting 4 wrong binds, then ONE CORRECT one.\n\n'
out=$(bindas "$CUR"); rc=$?
if [ $rc -ne 0 ]; then
    huh "correct password did not bind BEFORE the test (rc=$rc) — cannot test lockout"
else
    for i in 1 2 3 4; do bindas "definitely-the-wrong-password-$i" >/dev/null 2>&1; done
    printf '  4 failed binds submitted. accountUnlockTime: %s\n' \
        "$(ldapsearch -LLL -Y EXTERNAL -H "$LDAPI" -b "$DN" -s base accountUnlockTime passwordRetryCount 2>/dev/null | grep -E '^(accountUnlockTime|passwordRetryCount)' | tr '\n' ' ')"
    out=$(bindas "$CUR"); rc=$?
    if [ $rc -eq 0 ]; then
        bad "correct password ACCEPTED after 4 failures — directory lockout is NOT enforced"
    elif echo "$out" | grep -qiE 'retry limit|locked|constraint'; then
        ok "correct password refused while locked: $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
    else
        huh "correct password refused, but NOT for lockout (rc=$rc): $(echo "$out" | tr '\n' ' ' | cut -c1-150)"
    fi
fi

rule; printf '  SUMMARY\n'; rule
printf '  PASS %s   FAIL %s   INCONCLUSIVE %s\n' "$PASS" "$FAIL" "$INCONCLUSIVE"
printf '  (Test 1 is observational; Tests 2 and 3 are the POA&M-013 directory half.)\n'
printf '\n  NOTE: failed binds WILL appear in the Wazuh alert stream. Expected.\n'
