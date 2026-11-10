#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# 3.8.3 drill on DISPOSABLE disk images only (never touches real media). Passphrases are random, never written to a file or printed.
set -u
W=${1:-/tmp/diwai-sanitize-drill}; rm -rf "$W"; mkdir -p "$W"; cd "$W"
MARK="DIWAI-SANITIZE-MARKER-$(openssl rand -hex 8)"
PW=$(openssl rand -hex 16)
raw_has(){ LC_ALL=C grep -c -a "$MARK" "$1" 2>/dev/null | head -1; }
echo "== MEDIA SANITIZATION DRILL $(date '+%F %T')  marker length ${#MARK}"
echo; echo "-- TEST 1: unencrypted disposable image; overwrite (clear) method, WITH positive control"
hdiutil create -size 8m -fs APFS -volname DRILL1 -type UDIF -o plain.dmg >/dev/null 2>&1
M1=$(hdiutil attach plain.dmg -nobrowse 2>/dev/null | awk -F'\t' '/Volumes/{print $3}'); echo "$MARK" > "$M1/cui-test.txt"; sync; hdiutil detach "$M1" >/dev/null 2>&1
echo "marker found in the raw image BEFORE sanitization (positive control): $(raw_has plain.dmg)   (>=1 expected)"
SZ=$(stat -f %z plain.dmg); dd if=/dev/urandom of=plain.dmg bs=1m count=$((SZ/1048576+1)) conv=notrunc 2>/dev/null
echo "marker found in the raw image AFTER overwrite: $(raw_has plain.dmg)   (0 expected)"
echo; echo "-- TEST 2: encrypted disposable image; cryptographic erase (destroy the key), with a positive control"
echo -n "$PW" | hdiutil create -size 8m -fs APFS -volname DRILL2 -encryption AES-256 -stdinpass -type UDIF -o enc.dmg >/dev/null 2>&1
M2=$(echo -n "$PW" | hdiutil attach enc.dmg -stdinpass -nobrowse 2>/dev/null | awk -F'\t' '/Volumes/{print $3}'); echo "$MARK" > "$M2/cui-test.txt"; sync; hdiutil detach "$M2" >/dev/null 2>&1
echo "marker in the raw encrypted image (plaintext at rest): $(raw_has enc.dmg)   (0 expected: encryption holds)"
echo "mount WITH the key (positive control): $(echo -n "$PW" | hdiutil attach enc.dmg -stdinpass -nobrowse >/dev/null 2>&1 && echo MOUNTS || echo FAILS)"; hdiutil detach "$(hdiutil info | awk '/DRILL2/{f=1} f&&/\/dev\/disk[0-9]+\t/{print $1; exit}')" >/dev/null 2>&1 || hdiutil detach -force "$M2" >/dev/null 2>&1
PW=""; unset PW
echo "key destroyed (the only copy was in memory and is now unset)"
echo "mount WITHOUT the key: $(echo -n "wrong-$(openssl rand -hex 8)" | hdiutil attach enc.dmg -stdinpass -nobrowse >/dev/null 2>&1 && echo MOUNTS || echo REFUSED)"
echo; echo "-- CLEAN-UP"
hdiutil detach /Volumes/DRILL1 -force >/dev/null 2>&1; hdiutil detach /Volumes/DRILL2 -force >/dev/null 2>&1
rm -rf "$W"; echo "drill files removed: $([ -e "$W" ] && echo NO || echo yes)"; echo "images still attached: $(hdiutil info | grep -c 'DRILL')"
