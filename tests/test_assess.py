"""The per-requirement runner. Fake model, fake server: no test reaches LM Studio or the VM."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import assess  # noqa: E402
import grade  # noqa: E402

HERE = Path(__file__).resolve().parents[1]


def call(name, args, i=1):
    return {"id": f"c{i}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


def scripted(*turns):
    """A fake model that answers with the given assistant messages in order, recording what it was sent."""
    sent, it = [], iter(turns)

    def transport(payload):
        sent.append(json.loads(json.dumps(payload)))
        return {"choices": [{"message": next(it)}]}
    transport.sent = sent
    return transport


REC_311 = [{"objective": f"3.1.1[{x}]", "status": "Met", "source": "host", "evidence": "getent passwd shows one user"}
           for x in "abcdef"]


def test_kit_has_110_requirements_and_320_objectives():
    reqs = assess.requirements((HERE / "objectives.md").read_text())
    assert len(reqs) == 110 and sum(len(r["objectives"]) for r in reqs) == 320
    assert reqs[0]["id"] == "3.1.1" and reqs[0]["objectives"][0][0] == "3.1.1[a]"
    single = next(r for r in reqs if r["id"] == "3.13.4")
    assert [o[0] for o in single["objectives"]] == ["3.13.4"]


def test_a_round_runs_listed_commands_and_records(tmp_path):
    ran = []
    model = scripted(
        {"role": "assistant", "content": "", "tool_calls": [call("run_on_server", {"command": "getent passwd"})]},
        {"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311}, 2)]})
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: ran.append(c) or "alice:x:1000",
                        ask=lambda c, r: False, docs=HERE / "docs")
    out = assess.run_requirement(req, cfg)
    assert ran == ["getent passwd"] and out["status"] == "recorded"
    assert json.loads((tmp_path / "3.1.1.json").read_text())["results"][0]["status"] == "Met"
    assert "alice:x:1000" in model.sent[1]["messages"][-1]["content"]      # the output went back to the model


def test_secret_reads_never_run_and_unlisted_commands_ask_the_person(tmp_path):
    ran, asked = [], []
    model = scripted(
        {"role": "assistant", "content": "", "tool_calls": [call("run_on_server", {"command": "cat /etc/shadow"}),
                                                            call("run_on_server", {"command": "systemctl restart sshd"}, 2)]},
        {"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311}, 3)]})
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: ran.append(c) or "x",
                        ask=lambda c, r: asked.append(c) or False, docs=HERE / "docs")
    assess.run_requirement(req, cfg)
    assert ran == [] and asked == ["systemctl restart sshd"]
    replies = [m["content"] for m in model.sent[1]["messages"] if m["role"] == "tool"]
    assert any("refused" in r for r in replies) and any("declined" in r for r in replies)
    log = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert {e["verdict"] for e in log if e["tool"] == "run_on_server"} == {"refuse", "ask"}


def test_incomplete_records_are_sent_back_not_accepted(tmp_path):
    model = scripted(
        {"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311[:2]})]},
        {"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311}, 2)]})
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: "", ask=lambda c, r: False, docs=HERE / "docs")
    assert assess.run_requirement(req, cfg)["status"] == "recorded"
    assert "missing" in [m["content"] for m in model.sent[1]["messages"] if m["role"] == "tool"][0]


def test_step_limit_leaves_objectives_unanswered_never_invents_a_status(tmp_path):
    loop = {"role": "assistant", "content": "", "tool_calls": [call("list_documents", {})]}
    model = scripted(*[loop] * 10)
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: "", ask=lambda c, r: False,
                        docs=HERE / "docs", max_steps=4)
    assert assess.run_requirement(req, cfg)["status"] == "no answer"
    assert not (tmp_path / "3.1.1.json").exists()


def test_documents_cannot_be_read_outside_docs():
    assert "outside" in assess.read_document(HERE / "docs", "../grade.py", 1, 10)
    assert "outside" in assess.read_document(HERE / "docs", "/etc/hosts", 1, 10)


def test_assembled_file_is_what_the_grader_reads(tmp_path):
    (tmp_path / "3.1.1.json").write_text(json.dumps({"requirement": "3.1.1", "results": REC_311}))
    reqs = assess.requirements((HERE / "objectives.md").read_text())
    md = assess.assemble(reqs, tmp_path)
    kit = grade.kit_ids((HERE / "objectives.md").read_text())
    rows, problems = grade.parse_ai(md, kit)
    assert len(rows) == 6 and rows["3.1.1[a]"] == ("Met", "host") and problems == []


def test_a_repeated_command_is_not_run_twice(tmp_path):
    ran = []
    model = scripted(
        {"role": "assistant", "content": "", "tool_calls": [call("run_on_server", {"command": "cat /etc/group"})]},
        {"role": "assistant", "content": "", "tool_calls": [call("run_on_server", {"command": "cat /etc/group"}, 2)]},
        {"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311}, 3)]})
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: ran.append(c) or "wheel:x:10",
                        ask=lambda c, r: False, docs=HERE / "docs")
    assess.run_requirement(req, cfg)
    assert ran == ["cat /etc/group"]
    assert "already ran" in [m["content"] for m in model.sent[2]["messages"] if m["role"] == "tool"][-1]


def test_a_full_memory_trims_old_output_and_asks_for_the_record(tmp_path):
    big = "x" * 5000
    turns = [{"role": "assistant", "content": "", "tool_calls": [call("run_on_server", {"command": f"cat /etc/f{i}"}, i)]}
             for i in range(8)]
    turns.append({"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311}, 99)]})
    model = scripted(*turns)
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: big, ask=lambda c, r: False,
                        docs=HERE / "docs", budget_chars=20000)
    assert assess.run_requirement(req, cfg)["status"] == "recorded"
    last = model.sent[-1]["messages"]
    assert sum(len(m.get("content") or "") for m in last) <= 20000 + 6500     # stays near the budget
    assert any("removed to save space" in (m.get("content") or "") for m in last)
    assert any("record_results now" in (m.get("content") or "") for m in last)     # on a tool result or a user turn


def test_a_rejected_request_is_retried_once_with_less_memory(tmp_path):
    import urllib.error
    calls = {"n": 0}

    def flaky(payload):
        calls["n"] += 1
        if calls["n"] == 2:
            raise urllib.error.HTTPError("u", 400, "Bad Request", {}, None)
        if calls["n"] == 1:
            return {"choices": [{"message": {"role": "assistant", "content": "",
                                             "tool_calls": [call("run_on_server", {"command": "cat /etc/x"})]}}]}
        return {"choices": [{"message": {"role": "assistant", "content": "",
                                         "tool_calls": [call("record_results", {"results": REC_311}, 2)]}}]}
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=flaky, host=lambda c: "y" * 3000, ask=lambda c, r: False,
                        docs=HERE / "docs")
    assert assess.run_requirement(req, cfg)["status"] == "recorded"


def test_no_user_message_ever_follows_a_tool_result(tmp_path):
    # Mistral-family templates reject user-after-tool (LM Studio 400, seen live with Devstral 2026-10-05)
    loop = [{"role": "assistant", "content": "", "tool_calls": [call("run_on_server", {"command": f"cat /etc/f{i}"}, i)]}
            for i in range(5)]
    model = scripted(*loop, {"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": REC_311}, 9)]})
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: "z" * 5000, ask=lambda c, r: False,
                        docs=HERE / "docs", max_steps=6, budget_chars=12000)
    assert assess.run_requirement(req, cfg)["status"] == "recorded"
    for payload in model.sent:
        roles = [m["role"] for m in payload["messages"]]
        assert not any(a == "tool" and b == "user" for a, b in zip(roles, roles[1:])), roles
    joined = " ".join(m["content"] for m in model.sent[-1]["messages"] if m["role"] == "tool")
    assert "record_results now" in joined                                  # the reminder still reached it


def test_asking_the_person_speaks_an_alert_without_touching_the_real_speaker(monkeypatch):
    spoken = []
    monkeypatch.setattr(assess.subprocess, "Popen", lambda argv, **kw: spoken.append(argv))
    monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(OSError("no tty in tests")))
    assert assess._ask_person("systemctl restart sshd", "can change something") is False
    assert spoken and spoken[0][0] == "/usr/bin/say" and "Terminal" in " ".join(spoken[0])


def test_rev3_kit_has_97_requirements_and_510_objectives_including_the_parameters():
    reqs = assess.requirements((HERE / "kit-r3" / "objectives.md").read_text())
    ids = [o[0] for r in reqs for o in r["objectives"]]
    assert len(reqs) == 97 and len(ids) == 510 and len(set(ids)) == 510
    assert reqs[0]["id"] == "03.01.01"
    assert "A.03.01.01.ODP.01" in ids and "A.03.01.01.b.01" in ids
    assert sum(1 for i in ids if ".ODP." in i) == 88


def test_rev2_kit_parsing_is_unchanged_by_the_rev3_pattern():
    reqs = assess.requirements((HERE / "objectives.md").read_text())
    assert len(reqs) == 110 and sum(len(r["objectives"]) for r in reqs) == 320


def test_rev3_rounds_carry_the_parameter_rule_and_rev2_rounds_do_not(tmp_path):
    req = assess.requirements((HERE / "kit-r3" / "objectives.md").read_text())[0]
    for rev3 in (True, False):
        model = scripted(*[{"role": "assistant", "content": "", "tool_calls": [call("record_results", {"results": []})]}] * 90)
        cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: "", ask=lambda c, r: False,
                            docs=HERE / "docs", max_steps=1, rev3=rev3)
        assess.run_requirement(req, cfg)
        system = model.sent[0]["messages"][0]["content"]
        assert ("ODP" in system) == rev3


def test_the_last_steps_offer_only_the_record_tool(tmp_path):
    loop = {"role": "assistant", "content": "", "tool_calls": [call("list_documents", {})]}
    model = scripted(*[loop] * 10)
    req = assess.requirements((HERE / "objectives.md").read_text())[0]
    cfg = assess.Config(results=tmp_path, transport=model, host=lambda c: "", ask=lambda c, r: False,
                        docs=HERE / "docs", max_steps=6)
    assess.run_requirement(req, cfg)
    names = [[t["function"]["name"] for t in p["tools"]] for p in model.sent]
    assert len(names[0]) > 1 and names[3] == names[4] == names[5] == ["record_results"][:1] or \
        names[-1] == ["record_results"]
    assert names[-1] == ["record_results"] and names[-2] == ["record_results"]


def test_big_requirements_get_more_steps():
    small = assess.requirements((HERE / "objectives.md").read_text())[0]            # 6 objectives
    big = assess.requirements((HERE / "kit-r3" / "objectives.md").read_text())[0]   # 03.01.01: dozens
    assert assess.steps_for(big, 24) > assess.steps_for(small, 24) >= 24


def test_rev3_placeholders_name_the_parameter_they_depend_on():
    text = (HERE / "kit-r3" / "objectives.md").read_text()
    assert "[A.03.01.01.ODP.01: time period]" in text            # inactivity period (cross-checked with the register)
    assert "[organization-defined:" not in text
    reqs = assess.requirements(text)
    ids = {o for r in reqs for o, _ in r["objectives"]}
    assert ids >= {"A.03.01.01.ODP.01", "A.03.01.01.f.02"}
