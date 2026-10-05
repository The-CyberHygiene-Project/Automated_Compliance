"""The read-only command list: what runs on its own, what asks a person, what is refused.
Run: python3 -m pytest -q tests"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import allowlist as al  # noqa: E402

AUTO = [
    "cat /etc/ssh/sshd_config", "cat /etc/ssh/ssh_host_ecdsa_key.pub", "ls -la /etc/sssd", "getent passwd", "id alice", "stat /etc/shadow",
    "systemctl status sshd", "systemctl is-enabled firewalld", "systemctl list-timers --all",
    "getenforce", "sestatus", "fips-mode-setup --check", "update-crypto-policies --show",
    "firewall-cmd --list-all", "ss -tlnp", "ip addr show", "rpm -qa", "rpm -q openssh-server",
    "dnf updateinfo list --security", "chronyc tracking", "journalctl -u sshd -n 50", "grep -i PermitRootLogin /etc/ssh/sshd_config",
    "find /etc -name *.conf -newer /etc/hostname", "sysctl kernel.randomize_va_space", "crontab -l",
    "ldapsearch -x -H ldaps://localhost -b dc=example,dc=org '(objectClass=person)' uid", "usbguard list-rules",
    "sudo -n auditctl -l", "cut -d: -f1 /etc/passwd", "head -50 /etc/login.defs", "chage -l alice", "openssl x509 -noout -enddate -in /etc/pki/tls/certs/server.crt",
]

REFUSE = [
    "cat /etc/shadow", "sudo -n cat /etc/gshadow", "cat /etc/pki/tls/private/server.key", "cat /root/.ssh/id_rsa",
    "cat /etc/dirsrv/slapd-example/pin.txt", "grep -r password /etc", "head /home/alice/.ssh/id_ecdsa",
    "ldapsearch -x -D cn=admin -w hunter2 -b dc=example,dc=org", "cat /etc/sssd/sssd.conf",
    "openssl rsa -in /etc/pki/tls/private/server.key", "cat /etc/ssh/ssh_host_ecdsa_key", "sudo -n cat /etc/ssh/ssh_host_ed25519_key",
]

ASK = [
    "rm -rf /tmp/x", "systemctl restart sshd", "dnf install nmap", "find / -name x -delete", "find /etc -exec cat {} ;",
    "sysctl -w kernel.x=1", "sysctl kernel.x=1", "firewall-cmd --add-port=22/tcp", "chronyc makestep",
    "journalctl --vacuum-time=1d", "cat /etc/passwd; rm -rf /", "cat /etc/passwd | mail x", "cat $(echo /etc/passwd)",
    "echo hi > /tmp/x", "curl http://example.com", "crontab -r", "faillock --reset", "usbguard allow-device 3",
    "python3 -c print(1)", "sudo cat /etc/ssh/sshd_config", "ip link set eth0 down", "",
]


@pytest.mark.parametrize("cmd", AUTO)
def test_read_only_commands_run_on_their_own(cmd):
    verdict, reason, _ = al.check(cmd)
    assert verdict == "auto", reason


@pytest.mark.parametrize("cmd", REFUSE)
def test_secret_reads_are_refused_outright(cmd):
    assert al.check(cmd)[0] == "refuse"


@pytest.mark.parametrize("cmd", ASK)
def test_anything_else_needs_a_person(cmd):
    assert al.check(cmd)[0] == "ask"


def test_the_command_sent_is_requoted_so_the_server_shell_cannot_reinterpret_it():
    verdict, _, safe = al.check("grep -i 'permit root' /etc/ssh/sshd_config")
    assert verdict == "auto" and safe == "grep -i 'permit root' /etc/ssh/sshd_config"


def test_globs_stay_unquoted_so_they_work():
    assert al.check("ls /etc/*.conf")[2] == "ls /etc/*.conf"
