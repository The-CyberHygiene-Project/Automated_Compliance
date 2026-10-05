#!/usr/bin/env python3
"""AI Bill of Materials for a local-AI assessment run: the model, the software around it, the settings, the prompts
and the data it was given, with SHA-256 fingerprints so someone else can check they have the same pieces.

    python3 aibom/make_aibom.py --model-key google/gemma-4-26b-a4b-qat --model-dir <folder holding the model files> \\
        [--source <where the files came from, e.g. a Hugging Face repo>] [--out aibom]

Writes AIBOM.md (to read) and aibom.cdx.json (CycloneDX 1.6, machine readable). It records no folder paths, serial
numbers or host names. Standard library only; macOS commands (sw_vers, sysctl) with LM Studio's `lms` for the model.
"""
import argparse
import datetime
import hashlib
import json
import plistlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def scrub(text):
    """Remove folder paths: '/Users/x/y/z' becomes '<path>/z'."""
    return re.sub(r"/(?:Users|home|private|var|opt)/[^\s]*/", "<path>/", text)


def hash_files(folder):
    out = []
    for p in sorted(Path(folder).iterdir()):
        if p.is_file() and not p.name.startswith("."):
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            out.append({"name": p.name, "sha256": h.hexdigest(), "bytes": p.stat().st_size})
    return out


def _run(argv):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def app_version(app):
    """Version string from a macOS app's Info.plist (blank if the app is not there)."""
    try:
        return plistlib.loads((Path(app) / "Contents" / "Info.plist").read_bytes()).get("CFBundleShortVersionString", "")
    except (OSError, ValueError):
        return ""


def git_commit(folder):
    """Short commit id of the repository in `folder`, or blank (never an error message)."""
    try:
        r = subprocess.run(["git", "-C", str(folder), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def parse_version(text):
    """First version number in noisy CLI output (banner art, escape codes), without a build suffix."""
    m = re.search(r"(?<![\w.])(\d+\.\d+\.\d+)(?:\+\d+)?", re.sub(r"\x1b\[[0-9;]*m", "", text or ""))
    return m.group(1) if m else ""


def gather(model_key, model_dir, source=""):
    import assess
    src = (ROOT / "assess.py").read_text()
    sh = (ROOT / "assess.sh").read_text()

    def num(pattern, text, cast=float):
        m = re.search(pattern, text)
        return cast(m.group(1)) if m else None
    lms = Path.home() / ".lmstudio" / "bin" / "lms"
    meta = {}
    try:
        meta = next(x for x in json.loads(_run([str(lms), "ls", "--json"])) if x.get("modelKey") == model_key)
    except (StopIteration, ValueError):
        pass
    sw = {l.split(":")[0].strip(): l.split(":", 1)[1].strip() for l in _run(["sw_vers"]).splitlines() if ":" in l}
    lms_version = app_version("/Applications/LM Studio.app")
    ssh = _run(["/usr/bin/ssh", "-V"]).split(",")[0]
    data = []
    cat = ROOT / "reference" / "NIST_SP800-171_rev3_catalog.json"
    if cat.exists():
        d = json.loads(cat.read_text())["catalog"]["metadata"]
        data.append({"name": "NIST SP 800-171 Rev 3 OSCAL catalog", "version": d.get("version", ""), "sha256": _sha(cat)})
    for name, rel in (("Rev 3 objective kit", "kit-r3/objectives.md"), ("Rev 2 objective kit", "objectives.md")):
        if (ROOT / rel).exists():
            data.append({"name": name, "version": "generated; see kit header", "sha256": _sha(ROOT / rel)})
    commit = git_commit(ROOT)
    return {
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hardware": {"chip": _run(["sysctl", "-n", "machdep.cpu.brand_string"]),
                     "memory_gb": round(int(_run(["sysctl", "-n", "hw.memsize"]) or 0) / 2 ** 30)},
        "os": {"name": sw.get("ProductName", "macOS"), "version": sw.get("ProductVersion", "")},
        "software": [
            {"name": "LM Studio", "version": lms_version, "role": "serves the model locally (OpenAI-style API on localhost:1234)"},
            {"name": "Python", "version": sys.version.split()[0], "role": "runs the assessor, graders and tests"},
            {"name": "OpenSSH", "version": ssh.replace("OpenSSH_", ""), "role": "the one read-only connection to the target"},
            {"name": "macOS sandbox-exec", "version": sw.get("ProductVersion", ""), "role": "limits what the AI can read and reach"}],
        "model": {"key": model_key, "display": meta.get("displayName", model_key), "publisher": meta.get("publisher", ""),
                  "params": meta.get("paramsString", ""), "arch": meta.get("architecture", ""),
                  "quantization": (meta.get("quantization") or {}).get("name", ""), "format": meta.get("format", ""),
                  "context_max": meta.get("maxContextLength"), "source": source, "files": hash_files(model_dir)},
        "settings": {"temperature": num(r'"temperature":\s*([\d.]+)', src), "max_tokens": num(r'"max_tokens":\s*(\d+)', src, int),
                     "context_tokens": num(r"--context-length\s+(\d+)", sh, int),
                     "max_steps_base": num(r"max_steps=(\d+)", src, int), "budget_chars": num(r"budget_chars=(\d+)", src, int),
                     "tool_output_cap_chars": num(r"OUT_CAP\s*=\s*(\d+)", src, int)},
        "prompts": {"RULES": hashlib.sha256(assess.RULES.encode()).hexdigest(),
                    "REV3_RULE": hashlib.sha256(assess.REV3_RULE.encode()).hexdigest()},
        "data": data,
        "runner": {"commit": commit},
        "target": "a Linux server (read-only commands over SSH) plus a read-only copy of the organization's documents",
    }


def markdown(f):
    md, s = f["model"], f["settings"]
    L = ["# AI Bill of Materials: local-AI 800-171A assessment", "",
         f"Generated {f['generated']}. Machine-readable twin: `aibom.cdx.json` (CycloneDX 1.6). Regenerate for your own setup with "
         "`aibom/make_aibom.py`.", "", "## Model", "",
         "| | |", "|---|---|", f"| Name | {md['display']} |", f"| Catalog id | `{md['key']}` |", f"| Publisher | {md['publisher']} |",
         f"| Parameters | {md['params']} |", f"| Architecture | {md['arch']} |", f"| Quantization | {md['quantization']} |",
         f"| Format | {md['format']} |", f"| Maximum context | {md['context_max']} tokens |", f"| Files obtained from | {md['source'] or 'not recorded'} |", "",
         "SHA-256 of every model file (compare yours to confirm you have the same weights):", "", "| File | Bytes | SHA-256 |", "|---|---|---|"]
    L += [f"| {x['name']} | {x['bytes']} | `{x['sha256']}` |" for x in md["files"]]
    L += ["", "## Settings used", "", "| Setting | Value |", "|---|---|",
          f"| temperature | {s['temperature']} |", f"| max_tokens per reply | {s['max_tokens']} |",
          f"| context window loaded | {s['context_tokens']} tokens |", f"| base step limit per requirement | {s['max_steps_base']} (+1 per objective beyond six) |",
          f"| conversation budget | {s['budget_chars']} characters, older tool output trimmed |", f"| tool output cap | {s['tool_output_cap_chars']} characters |",
          "", "## Prompts", "", "SHA-256 of the instruction text the model receives (a change to either changes the result):", "",
          "| Prompt | SHA-256 |", "|---|---|"] + [f"| {k} | `{v}` |" for k, v in f["prompts"].items()]
    L += ["", "## Software", "", "| Component | Version | Role |", "|---|---|---|"]
    L += [f"| {x['name']} | {x['version']} | {x['role']} |" for x in f["software"]]
    L += [f"| Assessor (this repository) | commit {f['runner']['commit'] or 'unknown'} | the runner, command list, graders |"]
    L += ["", "## Hardware and operating system", "", f"- {f['hardware']['chip']}, {f['hardware']['memory_gb']} GB memory",
          f"- {f['os']['name']} {f['os']['version']}", "", "## Data given to the AI", "",
          "| Item | Version | SHA-256 |", "|---|---|---|"] + [f"| {x['name']} | {x['version']} | `{x['sha256']}` |" for x in f["data"]]
    L += ["", f"Target: {f['target']}.", "",
          "## What is not in this list", "", "- The organization's own documents and the answer keys (private by design).",
          "- Anything the model learned in training: the publisher's model card is the source for that.", ""]
    return scrub("\n".join(L))


def cyclonedx(f):
    md = f["model"]
    model = {"type": "machine-learning-model", "bom-ref": "model", "name": md["display"], "publisher": md["publisher"],
             "description": f"{md['params']} parameters, {md['quantization']}, {md['arch']}; catalog id {md['key']}",
             "modelCard": {"modelParameters": {"architectureFamily": md["arch"]}},
             "externalReferences": [{"type": "distribution", "url": md["source"]}] if md["source"] else [],
             "components": [{"type": "file", "name": x["name"], "hashes": [{"alg": "SHA-256", "content": x["sha256"]}]}
                            for x in md["files"]]}
    comps = [model, {"type": "device", "name": f["hardware"]["chip"], "description": f"{f['hardware']['memory_gb']} GB memory"},
             {"type": "operating-system", "name": f["os"]["name"], "version": f["os"]["version"]}]
    comps += [{"type": "application", "name": x["name"], "version": x["version"], "description": x["role"]} for x in f["software"]]
    comps += [{"type": "data", "name": x["name"], "version": x["version"], "hashes": [{"alg": "SHA-256", "content": x["sha256"]}]}
              for x in f["data"]]
    comps += [{"type": "data", "name": f"prompt {k}", "hashes": [{"alg": "SHA-256", "content": v}]} for k, v in f["prompts"].items()]
    return {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
            "metadata": {"timestamp": f["generated"], "component": {"type": "application", "name": "Automated_Compliance",
                         "version": f["runner"]["commit"] or "unknown"}}, "components": comps,
            "properties": [{"name": f"setting.{k}", "value": str(v)} for k, v in f["settings"].items()]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-key", required=True)
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--source", default="")
    ap.add_argument("--out", default=str(ROOT / "aibom"))
    a = ap.parse_args(argv)
    facts = gather(a.model_key, a.model_dir, a.source)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "AIBOM.md").write_text(markdown(facts))
    (out / "aibom.cdx.json").write_text(json.dumps(cyclonedx(facts), indent=1))
    print(f"Wrote {out / 'AIBOM.md'} and {out / 'aibom.cdx.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
