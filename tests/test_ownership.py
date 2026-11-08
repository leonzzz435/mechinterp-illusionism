import hashlib
import json
from collections import Counter
from copy import deepcopy

import pytest

from self_model_study import ownership as o
from self_model_study.action_task import score_command
from self_model_study.io import digest, write_json
from self_model_study.ownership_reporting import export, summarize
from self_model_study.pilot import jobs_in
from self_model_study.storage import read_records


@pytest.fixture(scope="module")
def plans():
    return [o.build_plan(o.configuration(i)) for i in range(3)]


def test_frozen_assignment_inventory_independent_oracle_and_input_boundary(plans):
    d = o.design()
    expected_actor = sorted(
        d["sample"]["actor_labels"],
        key=lambda s: hashlib.sha256(
            json.dumps(
                [94173, "ownership-v1:0000", s], sort_keys=True, ensure_ascii=False, allow_nan=False
            ).encode()
        ).hexdigest(),
    )[:2]
    assert o.world(0)[1] == expected_actor == ["Lynx", "Kestrel"]
    assert [digest(p) for p in plans] == [
        "968ce4e39e6ead100f0e13a003ef11b0f63a377d4d3463a463bf2b1311cffac7",
        "0a276fcae40e0e8dc436fa6c3d467fa84d92aa06259b193bd1ff45151cdeaf81",
        "5a7bc5ec284d2eb1de2879637b7b71324a621eeee9263580b479734e470dc6e9",
    ]
    jobs = [j for p in plans for j in jobs_in(p)]
    assert len(jobs) == len({j["id"] for j in jobs}) == 18432
    assert len({j["row"]["scenario_id"] for j in jobs}) == 48
    for p in plans:
        assert len(jobs_in(p)) == 6144
    for block in [b for p in plans for b in p["blocks"]]:
        rows = [j["row"] for j in block["jobs"]]
        assert Counter(r["expected_position"] for r in rows) == {i: 96 for i in range(4)}
        assert set(Counter((r["frame"], r["relation"]) for r in rows).values()) == {64}
        for row in rows:
            # Independently reconstruct the successful command from initial facts and update.
            expected = (
                row["event"]["grant"]
                if row["phase"] == "after" and row["target"] == row["event"]["actor"]
                else row["before"]["permissions"][row["target"]][0]
            )
            assert row["expected_command"] == expected
            assert [c for c in row["choices"] if score_command(row, c)["correct"]] == [expected]
            assert row["prompt"].endswith("Selected command:\n")
            assert f"Query account: {row['target']}\n" in row["prompt"]
            assert not any(
                k in row["prompt"]
                for k in ("scenario_id", "expected_command", "relevant_update", "ownership-v1:")
            )
            assert row["prompt"].startswith("Two operators are mentioned: you and observer Rowan.")


def test_frozen_config_rejects_model_prompt_sample_and_time_changes():
    for key, val in [
        ("task_template", "tool_routing"),
        ("world_indices", [0]),
        ("score", "mean"),
        ("max_seconds", 7200),
        ("model", {}),
    ]:
        with pytest.raises(ValueError):
            o.validate_spec({**o.configuration(0), key: val})
    with pytest.raises(ValueError):
        o.configuration(3)


def test_overlap_checks_context_stripped_inputs():
    old = "Your active connection: Lynx.\nQuery account: Lynx\n"
    changed = "Their active connection: Kestrel.\nQuery account: Lynx\n"
    with pytest.raises(ValueError, match="collision"):
        o.check_overlap([old], {old}, set())
    with pytest.raises(ValueError, match="collision"):
        o.check_overlap([changed], {old}, {o.without_context(old)})
    o.check_overlap([changed + "different facts"], {old}, {o.without_context(old)})


def test_categorical_precedence_and_counterfactual_updates(plans):
    row = next(
        j["row"]
        for j in jobs_in(plans[0])
        if j["row"]["phase"] == "after" and j["row"]["relevant_update"]
    )
    target = row["target"]
    other = next(a for a in row["state"]["permissions"] if a != target)
    for cmd, category in [
        (row["expected_command"], "correct_target_current"),
        (row["state"]["permissions"][other][0], "other_account_current"),
        (row["before"]["permissions"][target][0], "revoked_target"),
    ]:
        assert o.classify(row, {"status": "ok", "selected_command": cmd}) == category
    assert o.classify(row, {"status": "tie", "selected_command": None}) == "invalid"
    assert o.classify(row, None) == "missing"
    assert o.classify(row, {"status": "ok", "selected_command": "injected_unknown"}) == "invalid"
    before = deepcopy(row)
    before["phase"] = "before"
    before["state"] = row["before"]
    assert (
        o.classify(
            before, {"status": "ok", "selected_command": before["state"]["permissions"][target][0]}
        )
        == "correct_target_current"
    )
    variants = [
        j["row"]
        for j in jobs_in(plans[0])
        if j["row"]["scenario_id"] == row["scenario_id"]
        and j["row"]["phase"] == "after"
        and j["row"]["target_identity"] == row["target_identity"]
        and j["row"]["updated"] == row["updated"]
        and j["row"]["rotation"] == row["rotation"]
        and j["row"]["frame"] == row["frame"]
        and j["row"]["relation"] == row["relation"]
    ]
    assert len(variants) == 2 and len({r["expected_command"] for r in variants}) == 2


class Fake:
    def choice(self, prompt, choices, format_name):
        assert isinstance(prompt, str) and len(choices) == 4 and format_name == "chat"
        return {
            "status": "ok",
            "selected_command": choices[0],
            "candidates": [
                {"command": c, "log_likelihood": -float(i + 1), "token_ids": [i], "token_count": 1}
                for i, c in enumerate(choices)
            ],
        }


def fake_factory(_):
    return Fake(), {"synthetic": True}


def test_resume_atomic_journal_errors_export_and_no_false_complete(tmp_path):
    spec = o.configuration(0)
    path = tmp_path / "run"
    m = o.run(spec, path, max_jobs=1, backend_factory=fake_factory)
    assert m["status"] == "paused" and len(m["records"]) == 1
    m["records"] = {}
    write_json(path / "manifest.json", m)
    m = o.run(spec, path, max_jobs=2, backend_factory=fake_factory)
    assert len(read_records(path)) == len(m["records"]) == 3
    report = summarize([o.read_run(path)])
    assert not report["complete"] and report["recorded_choices"] == 3
    assert report["primary"]["ci95"] is None
    assert sum(v["counts"]["missing"] for v in report["cells"].values()) == 6141
    a = export(path, tmp_path / "one.tar.gz")
    b = export(path, tmp_path / "two.tar.gz")
    assert a["sha256"] == b["sha256"]
    with pytest.raises(ValueError, match="Overlapping"):
        summarize([o.read_run(path), o.read_run(path)])

    class Invalid(Fake):
        def choice(self, *args):
            r = super().choice(*args)
            r["status"] = "invalid_scores"
            r["selected_command"] = None
            r["candidates"][0]["log_likelihood"] = None
            return r

    failed = o.run(
        spec,
        tmp_path / "failed",
        max_jobs=2,
        backend_factory=lambda _: (Invalid(), {"synthetic": True}),
    )
    assert failed["status"] == "failed" and len(failed["records"]) == 1
    with pytest.raises(ValueError, match="Failed run"):
        o.run(spec, tmp_path / "failed", backend_factory=fake_factory)


def test_actual_tokenizer_boundaries_and_output_audit(plans):
    pytest.importorskip("transformers")
    # Use the cached pinned tokenizer only; never download weights or run a pretrained model.
    from transformers import AutoTokenizer

    from self_model_study.pilot_backend import encode_boundary, render_prompt

    tokenizer = AutoTokenizer.from_pretrained(
        o.configuration(0)["model"]["repo"],
        revision=o.configuration(0)["model"]["revision"],
        local_files_only=True,
    )
    job = plans[0]["blocks"][0]["jobs"][0]
    row = job["row"]
    rendered = render_prompt(tokenizer, row["prompt"], "chat")
    encoded = [encode_boundary(tokenizer, rendered, c, 2048) for c in row["choices"]]
    for command, (ctx, cont) in zip(row["choices"], encoded):
        assert tokenizer.encode(rendered + command, add_special_tokens=False) == ctx + cont
        assert tokenizer.decode(cont) == command
    inputs = {
        row["prompt"]: {
            "rendered_prompt": rendered,
            "prompt_token_ids": encoded[0][0],
            "continuations": dict(zip(row["choices"], [x[1] for x in encoded])),
        }
    }
    result = {
        "rendered_prompt": rendered,
        "prompt_token_ids": encoded[0][0],
        "candidates": [
            {"command": c, "token_ids": v[1], "token_count": len(v[1])}
            for c, v in zip(row["choices"], encoded)
        ],
    }
    o.check_output(row, result, inputs)
    result["candidates"][0]["token_ids"] = []
    with pytest.raises(ValueError):
        o.check_output(row, result, inputs)


def test_complete_tranche_keeps_world_clusters_and_family_pending(plans):
    runs = []
    for i, plan in enumerate(plans):
        records = []
        for job in jobs_in(plan):
            r = job["row"]
            command = r["expected_command"]
            if (
                r["world_index"] < 24
                and r["relation"] == "target"
                and o.stratum(r) == "after_relevant"
            ):
                other = next(a for a in r["state"]["permissions"] if a != r["target"])
                command = r["state"]["permissions"][other][0]
            records.append(
                {"id": job["id"], "result": {"status": "ok", "selected_command": command}}
            )
        runs.append(
            (
                {
                    "run_id": str(i),
                    "status": "complete",
                    "synthetic": True,
                    "provenance": {"source_hash": "fixture"},
                },
                plan,
                records,
            )
        )
    report = summarize(runs)
    assert report["complete"] and report["independent_worlds"] == 48
    assert report["primary"]["estimate"] == 0.5 and report["controls_pass"]
    assert report["primary"]["ci95"][0] > 0 and report["primary"]["ci95"][1] < 1
    assert report["primary"]["unadjusted_t_p"] < 0.05
    assert "no_full_replication" in report["decision"]
    assert len(report["primary"]["world_contrasts"]) == 48
    assert sum(report["primary"]["world_contrasts"].values()) == 24
    assert (
        "pending" in report["primary"]["multiplicity_status"]
        or "incomplete" in report["primary"]["multiplicity_status"]
    )


def test_frozen_token_file_and_source_drift_block_before_scoring(plans, tmp_path, monkeypatch):
    import gzip

    from self_model_study.io import canonical, file_hash

    plan = plans[0]
    spec = o.configuration(0)
    inputs = {j["row"]["prompt"]: {"fixture": True} for j in jobs_in(plan)}
    token = tmp_path / "tokens.json.gz"
    token.write_bytes(gzip.compress(canonical(inputs).encode()))
    source = tmp_path / "generator.py"
    source.write_text("original")
    audit = tmp_path / "preflight.json"
    write_json(
        audit,
        {
            "design_sha256": o.DESIGN_SHA256,
            "blocks": [{"plan_hash": digest(plan), "token_inputs_hash": digest(inputs)}],
            "token_inputs_sha256": file_hash(token),
            "source_files": {"generator.py": file_hash(source)},
        },
    )
    monkeypatch.setattr(o, "PREFLIGHT", audit)
    monkeypatch.setattr(o, "INPUTS", token)
    monkeypatch.setattr(o, "ROOT", tmp_path)
    assert o.frozen_inputs(spec, plan)[0] == inputs
    source.write_text("changed")
    with pytest.raises(ValueError, match="source"):
        o.frozen_inputs(spec, plan)
    source.write_text("original")
    token.write_bytes(b"changed")
    with pytest.raises(ValueError, match="token inputs"):
        o.frozen_inputs(spec, plan)
