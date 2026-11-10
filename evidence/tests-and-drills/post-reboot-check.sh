#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# Read-only checks after a Mac host restart (DIWAI-CR-2026-10-01 reboot test,
# plus the DIWAI-CR-2026-10-02 additions). Changes nothing.
# Run it from Terminal:  ~/diwai/scripts/post-reboot-check.sh
# Exit status 0 = every check passed.

EXPECT_LMS_VERSION="0.4.25+1"
fails=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; fails=$((fails + 1)); }
info() { printf 'INFO  %s\n' "$1"; }

echo "Post-reboot check, $(date '+%Y-%m-%d %H:%M'); host up since $(sysctl -n kern.boottime | sed 's/.*} //')"

# 1. LM Studio version unchanged (the app can stage its own updates).
v=$(defaults read "/Applications/LM Studio.app/Contents/Info" CFBundleShortVersionString 2>/dev/null)
[ "$v" = "$EXPECT_LMS_VERSION" ] && pass "LM Studio version $v" || fail "LM Studio version is '$v', expected $EXPECT_LMS_VERSION"

# 2. LM Studio serves the models.
models=$(/usr/bin/curl -s -m 10 http://127.0.0.1:1234/v1/models)
for m in mistralai/devstral-small-2-2512 text-embedding-nomic-embed-text-v1.5@f16; do
    echo "$models" | /usr/bin/grep -q "\"$m\"" && pass "LM Studio lists $m" || fail "LM Studio does not list $m"
done

# 3. (LM Studio 0.4 runs its window and server in one --run-as-service process,
#    so "is the window open" cannot be told apart here; check 2 is the proof
#    that the server answers.)

# 4. Devstral and the embedder stay loaded together.
jit=$(/usr/bin/python3 -c "import json;print(json.load(open('$HOME/.lmstudio/settings.json'))['developer'].get('unloadPreviousJITModelOnLoad'))" 2>/dev/null)
[ "$jit" = "False" ] && pass "LM Studio auto-evict is off" || fail "LM Studio unloadPreviousJITModelOnLoad is '$jit', expected False"

# 5. Listeners: loopback only; retired ports silent.
for p in 1234 3000 8767; do
    addrs=$(/usr/sbin/lsof -nP -iTCP:$p -sTCP:LISTEN 2>/dev/null | /usr/bin/awk 'NR>1{print $9}' | sort -u | tr '\n' ' ')
    if [ -z "$addrs" ]; then fail "nothing listening on $p"
    elif echo "$addrs" | /usr/bin/grep -qv '^127\.0\.0\.1:' ; then
        echo "$addrs" | tr ' ' '\n' | /usr/bin/grep -v '^$' | /usr/bin/grep -qv '^127\.0\.0\.1:' && fail "port $p listens beyond loopback: $addrs" || pass "port $p on 127.0.0.1 only"
    else pass "port $p on 127.0.0.1 only"; fi
done
for p in 11434 8081 4000; do
    /usr/sbin/lsof -nP -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1 && fail "retired port $p is listening" || pass "retired port $p silent"
done

# 6. Background services loaded.
for a in org.diwai.lmstudio org.diwai.open-webui org.diwai.rag-mcp; do
    launchctl print "gui/$(id -u)/$a" >/dev/null 2>&1 && pass "LaunchAgent $a loaded" || fail "LaunchAgent $a not loaded"
done

# 7. Open WebUI answers.
code=$(/usr/bin/curl -s -m 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/health)
[ "$code" = "200" ] && pass "Open WebUI health 200" || fail "Open WebUI health returned $code"

# 8. The document library answers through its MCP server.
docs=$(cd "$HOME/diwai-rag" && venv/bin/python - <<'EOF' 2>/dev/null
import anyio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
async def main():
    async with streamable_http_client("http://127.0.0.1:8767/mcp") as s:
        async with ClientSession(s[0], s[1]) as c:
            await c.initialize()
            print((await c.call_tool("list_documents", {})).content[0].text.split()[0])
anyio.run(main)
EOF
)
case "$docs" in ''|*[!0-9]*|0) fail "library MCP server did not answer with a document count ('$docs')";;
                *) pass "library MCP server answers: $docs documents";; esac

# 9. The VM is unlocked and serving (webmail behind nginx on the VM).
vm=$(/usr/bin/curl -sk -m 10 -o /dev/null -w '%{http_code}' -H 'Host: webmail.[DOMAIN.ORG]' https://[LAN-IP-REDACTED]/)
case "$vm" in 2*|3*|401) pass "VM web service answers ($vm)";;
             *) fail "VM web service returned '$vm' (still at the disk-passphrase prompt?)";; esac

echo
[ "$fails" -eq 0 ] && echo "ALL CHECKS PASSED" || echo "$fails CHECK(S) FAILED"
exit "$fails"
