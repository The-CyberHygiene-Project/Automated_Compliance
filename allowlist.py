"""The read-only command list for the 800-171A test (owner decision 2026-10-05, option B).

check(command) -> (verdict, reason, command_to_send)
    "auto"   a read-only command on the list: runs without asking
    "refuse" reads a secret (password hashes, private keys, credentials): never runs
    "ask"    anything else, including pipes, redirects and anything unknown: a person decides

The command is split the way a shell would and re-quoted before it is sent, so the server's shell cannot read
an argument as an operator. Pipes, redirects, ';', '&&', '$(' and backticks are never auto-run.
"""
import re
import shlex

SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_./*?=:,@+%-]+$")      # sent as is (keeps globs working)
OPERATORS = set(";&|<>()")

# Paths and words that mean a secret. Only matter for commands that print file contents or bind credentials.
SECRET_PATH = re.compile(
    r"(^|/)g?shadow-?$|/private/|\.key$|_key$|(^|/)id_(rsa|ecdsa|ed25519|dsa)$|pin\.txt$|sssd\.conf$|\.p12$|\.pfx$"
    r"|keytab|\.htpasswd$|\.netrc$|authd\.pass$|client\.keys$|credential|secret|\.pgpass$|my\.cnf$", re.I)
SECRET_WORD = re.compile(r"passw(or)?d\b(?!$)|^password$|^passwords?$|secret|private.?key|token", re.I)
READERS = {"cat", "head", "tail", "grep", "egrep", "fgrep", "strings", "xxd", "od", "base64", "less", "more",
           "sed", "awk", "diff", "cmp", "openssl", "find"}

SIMPLE = {"cat", "ls", "stat", "getent", "id", "head", "tail", "wc", "uname", "hostname", "getenforce", "sestatus",
          "df", "lsblk", "who", "w", "last", "lastlog", "uptime", "date", "grep", "egrep", "fgrep", "file",
          "readlink", "findmnt", "getfacl", "lsattr", "namei", "lscpu", "free", "ps", "whoami", "groups", "ss",
          "netstat", "cut", "ausearch", "aureport", "needs-restarting", "getsebool", "lsof", "sha256sum", "md5sum"}


def _sub(args):
    """First argument that is not an option."""
    return next((a for a in args if not a.startswith("-")), "")


def _rule(cmd, args):
    """True = read-only form of a listed command; None = not on the list."""
    sub = _sub(args)
    if cmd in SIMPLE:
        return True
    if cmd == "rpm":
        return bool(args) and all(a.startswith(("-q", "--query", "-V", "--verify")) or not a.startswith("-")
                                  for a in args) and args[0].startswith(("-q", "--query", "-V", "--verify"))
    if cmd == "systemctl":
        return sub in {"status", "is-active", "is-enabled", "is-failed", "show", "list-units", "list-unit-files",
                       "list-timers", "list-sockets", "cat", "get-default"}
    if cmd == "journalctl":
        return not any(a.startswith(("--vacuum", "--rotate", "--flush", "--relinquish", "--sync", "--setup-keys",
                                     "--update-catalog")) for a in args)
    if cmd == "find":
        return not any(a in {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fprint0",
                             "-fls"} for a in args)
    if cmd in {"dnf", "yum"}:
        if sub == "history":
            rest = args[args.index("history") + 1:]
            return not rest or _sub(rest) in {"list", "info", ""}
        return sub in {"list", "info", "updateinfo", "repolist", "repoquery", "check-update", "search", "provides"}
    if cmd == "firewall-cmd":
        return bool(args) and all(a.startswith(("--list", "--get", "--query", "--state", "--info", "--zone",
                                                "--permanent")) for a in args)
    if cmd == "sysctl":
        return not any(a in {"-w", "-p", "--system", "--load", "--write"} or "=" in a for a in args)
    if cmd == "chronyc":
        return sub in {"tracking", "sources", "sourcestats", "activity", "ntpdata", "serverstats"}
    if cmd == "fips-mode-setup":
        return args in (["--check"], ["--is-enabled"])
    if cmd == "update-crypto-policies":
        return args in (["--show"], ["--is-applied"], ["--check"])
    if cmd == "auditctl":
        return args in (["-l"], ["-s"])
    if cmd == "ldapsearch":
        return not any(a in {"-W"} for a in args)
    if cmd == "crontab":
        return "-l" in args and not any(a in {"-r", "-e", "-i"} for a in args)
    if cmd == "ip":
        verbs = [a for a in args if not a.startswith("-")]
        return bool(verbs) and verbs[0] in {"addr", "a", "address", "route", "r", "link", "l", "neigh", "rule"} \
            and all(v in {"show", "list", "ls"} for v in verbs[1:2])
    if cmd == "usbguard":
        return sub in {"list-devices", "list-rules", "get-parameter"}
    if cmd == "chage":
        return "-l" in args and len([a for a in args if a.startswith("-")]) == 1
    if cmd == "faillock":
        return "--reset" not in args
    if cmd == "openssl":
        return sub in {"x509", "version", "ciphers", "list"}
    if cmd == "semanage":
        return "-l" in args and not any(a in {"-a", "-d", "-m", "-D", "-C", "-E"} for a in args)
    if cmd == "authselect":
        return sub in {"current", "check", "list"}
    if cmd == "sshd":
        return args == ["-T"]
    if cmd in {"timedatectl", "hostnamectl"}:
        return sub in {"", "status", "show"}
    return None


def _secret(cmd, args):
    if cmd == "ldapsearch" and any(a in {"-w", "-y"} or a.startswith(("-w", "-y")) for a in args):
        return "a password on the command line"
    if cmd == "openssl" and _sub(args) in {"rsa", "pkey", "pkcs12", "ec", "genpkey"}:
        return "a private key"
    if cmd in READERS:
        for a in args:
            if SECRET_PATH.search(a):
                return f"secret file {a}"
        if cmd in {"grep", "egrep", "fgrep"} and any(a in {"-r", "-R", "-rn", "-ri", "-rl", "-Ri"} or
                                                     a.startswith(("-r", "-R")) for a in args) \
                and any(SECRET_WORD.search(a) for a in args if not a.startswith("-")):
            return "a search for passwords or secrets"
    return None


def check(command):
    command = (command or "").strip()
    if not command:
        return "ask", "empty command", ""
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError as exc:
        return "ask", f"could not be read safely ({exc})", command
    if any(t and set(t) <= OPERATORS for t in tokens):
        return "ask", "pipes, redirects or command separators are never run without a person", command
    if any("$" in t or "`" in t for t in tokens):
        return "ask", "shell substitution is never run without a person", command
    safe = " ".join(t if SAFE_TOKEN.match(t) else shlex.quote(t) for t in tokens)
    rest = tokens
    if rest[0] == "sudo":
        if len(rest) < 3 or rest[1] != "-n":
            return "ask", "sudo must be 'sudo -n' (it cannot prompt for a password here)", safe
        rest = rest[2:]
    cmd, args = rest[0], rest[1:]
    secret = _secret(cmd, args)
    if secret:
        return "refuse", f"refused: reads {secret}", safe
    ok = _rule(cmd, args)
    if ok:
        return "auto", "read-only command on the list", safe
    if ok is None:
        return "ask", f"'{cmd}' is not on the read-only list", safe
    return "ask", f"this form of '{cmd}' can change something", safe
