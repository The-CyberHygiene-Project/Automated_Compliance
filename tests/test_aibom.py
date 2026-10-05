import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "aibom"))
import make_aibom as m  # noqa: E402

FACTS = {
    "generated": "2026-10-05T12:00:00Z",
    "hardware": {"chip": "Apple M4 Pro", "memory_gb": 64},
    "os": {"name": "macOS", "version": "26.7"},
    "software": [{"name": "LM Studio", "version": "0.4.25", "role": "local model server"},
                 {"name": "Python", "version": "3.9.6", "role": "runs the assessor"}],
    "model": {"key": "vendor/model-26b", "display": "Model 26B", "publisher": "vendor", "params": "26B", "arch": "x",
              "quantization": "4bit", "format": "safetensors", "context_max": 262144, "source": "example-community/Model-26B-4bit",
              "files": [{"name": "a.safetensors", "sha256": "ab" * 32, "bytes": 10},
                        {"name": "config.json", "sha256": "cd" * 32, "bytes": 5}]},
    "settings": {"temperature": 0.2, "max_tokens": 8192, "context_tokens": 65536, "max_steps_base": 24,
                 "budget_chars": 120000, "tool_output_cap_chars": 6000},
    "prompts": {"RULES": "11" * 32, "REV3_RULE": "22" * 32},
    "data": [{"name": "NIST OSCAL catalog", "version": "1.1.0", "sha256": "33" * 32}],
    "runner": {"commit": "abc1234"},
    "target": "a Linux server reached over SSH, read-only",
}


def test_file_hashes_are_sha256_of_every_file_and_deterministic(tmp_path):
    (tmp_path / "x.bin").write_bytes(b"hello")
    (tmp_path / "y.json").write_text("{}")
    files = m.hash_files(tmp_path)
    assert [f["name"] for f in files] == ["x.bin", "y.json"]
    assert files[0]["sha256"] == hashlib.sha256(b"hello").hexdigest() and files[0]["bytes"] == 5


def test_cyclonedx_has_the_model_with_one_hash_per_file():
    cdx = m.cyclonedx(FACTS)
    assert cdx["bomFormat"] == "CycloneDX" and cdx["specVersion"] == "1.6"
    mdl = next(c for c in cdx["components"] if c["type"] == "machine-learning-model")
    assert mdl["name"] == "Model 26B" and mdl["publisher"] == "vendor"
    files = [c for c in mdl["components"] if c["type"] == "file"]
    assert [f["hashes"][0]["content"] for f in files] == ["ab" * 32, "cd" * 32]
    assert all(f["hashes"][0]["alg"] == "SHA-256" for f in files)
    types = {c["type"] for c in cdx["components"]}
    assert {"machine-learning-model", "application", "data", "device"} <= types


def test_markdown_states_model_settings_prompts_and_data():
    md = m.markdown(FACTS)
    for needle in ["Model 26B", "4bit", "ab" * 32, "temperature", "0.2", "65536", "RULES", "11" * 32,
                   "NIST OSCAL catalog", "1.1.0", "Apple M4 Pro", "LM Studio"]:
        assert needle in md, needle


def test_nothing_machine_specific_leaks_into_either_output(tmp_path):
    blob = m.markdown(FACTS) + json.dumps(m.cyclonedx(FACTS))
    assert "/Users/" not in blob and "/home/" not in blob
    assert m.scrub("loaded from /Users/someone/models/x") == "loaded from <path>/x"


def test_lm_studio_version_is_read_from_noisy_cli_output():
    noisy = "\x1b[38;5;166m   __   __  ___\x1b[0m\n  / /  /  |/  /\n0.4.25+1\nCLI commit: 69d945a\n"
    assert m.parse_version(noisy) == "0.4.25"
    assert m.parse_version("") == ""


def test_app_version_comes_from_the_apps_plist_and_a_missing_app_is_blank(tmp_path):
    import plistlib
    app = tmp_path / "X.app" / "Contents"
    app.mkdir(parents=True)
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleShortVersionString": "0.4.25+1"}))
    assert m.app_version(tmp_path / "X.app") == "0.4.25+1"
    assert m.app_version(tmp_path / "missing.app") == ""


def test_git_errors_never_leak_into_the_commit_field(tmp_path):
    assert m.git_commit(tmp_path) == ""            # not a repository: blank, not an error message
