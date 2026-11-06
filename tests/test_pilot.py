import csv
import json
from collections import Counter
from copy import deepcopy

import pytest

from self_model_study import pilot
from self_model_study.action_task import score_command
from self_model_study.io import canonical, digest, file_hash, read_json, write_json
from self_model_study.pilot_analysis import (
    counterfactuals,
    estimate,
    language_metrics,
    rating_lookup,
    read_ratings,
    summarize,
)
from self_model_study.pilot_backend import encode_boundary, render_prompt, select_command
from self_model_study.pilot_reporting import export, export_ratings
from self_model_study.storage import Journal, read_records


@pytest.fixture
def spec():
    return pilot.load_spec("configs/qwen-pilot.json")


class FakeBackend:
    def choice(self, prompt, choices, format_name):
        # The backend receives only strings, never a row, gold label or record ID.
        assert isinstance(prompt, str) and format_name in pilot.FORMATS
        assert len(choices) == 4 and all(isinstance(c, str) for c in choices)
        return {
            "status": "ok",
            "selected_command": choices[0],
            "candidates": [
                {"command": c, "token_count": 3, "token_ids": [1, 2, 3], "log_likelihood": -i - 1.0}
                for i, c in enumerate(choices)
            ],
        }

    def generate(self, prompt, format_name, seed):
        assert isinstance(prompt, str) and seed in {42, 43}
        return {"status": "ok", "output": "I am a language model."}


def fake_factory(_):
    return FakeBackend(), {"synthetic": True}


def test_fixed_development_plan_and_inputs(spec):
    plan = pilot.build_plan(spec)
    jobs = pilot.jobs_in(plan)
    assert plan == pilot.build_plan(spec)
    assert len(jobs) == len({j["id"] for j in jobs}) == 3232
    assert Counter(j["kind"] for j in jobs) == {"action": 3072, "language": 160}
    assert plan["prompt_hash"] == "32129c1e0fb1891bb60fb77c78c9e242713135b9a8488665a805855fc25dcc41"
    actions = [j for j in jobs if j["kind"] == "action"]
    assert len({j["row"]["scenario_id"] for j in actions}) == 8
    assert all(j["row"]["split"] == "development" for j in actions)
    assert Counter(j["row"]["expected_position"] for j in actions) == {i: 768 for i in range(4)}
    assert len(rating_lookup(jobs, {})) == 40
    for key, value in (
        ("score", "mean_log_likelihood"),
        ("num_fewshot", 4),
        ("scenarios", [0]),
        ("max_seconds", 7200),
    ):
        with pytest.raises(ValueError):
            pilot.validate_spec({**spec, key: value})


def test_resume_atomic_recovery_errors_and_no_duplicates(spec, tmp_path):
    path = tmp_path / "run"
    first = pilot.run(spec, path, max_jobs=1, backend_factory=fake_factory)
    assert first["status"] == "paused" and len(first["records"]) == 1
    # Simulate crash after a committed SQLite trial but before the manifest write.
    manifest = read_json(path / "manifest.json")
    manifest["records"] = {}
    write_json(path / "manifest.json", manifest)
    second = pilot.run(spec, path, max_jobs=20, backend_factory=fake_factory)
    assert len(second["records"]) == len(read_records(path)) == 21
    inputs = read_json(path / "model_inputs.json")
    assert all(set(r) <= {"id", "prompt", "format", "choices"} for r in inputs)
    assert not summarize(path)["action_gate_passed"]
    assert summarize(path)["language_effects"][0]["estimate"] is None
    with pytest.raises(ValueError, match="Frozen pilot"):
        pilot.run({**spec, "num_fewshot": 1}, path, backend_factory=fake_factory)
    original = read_json(path / "manifest.json")
    changed = deepcopy(original)
    changed["records"][next(iter(changed["records"]))] = "bad"
    write_json(path / "manifest.json", changed)
    with pytest.raises(ValueError, match="changed committed"):
        pilot.read_run(path)
    write_json(path / "manifest.json", original)
    changed = deepcopy(original)
    changed["provenance"]["source_hash"] = "changed-source"
    write_json(path / "manifest.json", changed)
    with pytest.raises(ValueError, match="source_hash changes"):
        pilot.run(spec, path, backend_factory=fake_factory)
    write_json(path / "manifest.json", original)

    class Broken(FakeBackend):
        def choice(self, *args):
            raise RuntimeError("fixture failure")

    failed = pilot.run(
        spec, path, max_jobs=1, backend_factory=lambda _: (Broken(), {"synthetic": True})
    )
    assert failed["status"] == "failed"
    assert len(read_records(path)) == 22
    assert summarize(path)["errors"] == 1
    with pytest.raises(ValueError, match="No automatic retry"):
        pilot.run(spec, path, backend_factory=fake_factory)


class CharTokenizer:
    chat_template = "fixture template"

    def encode(self, text, **_):
        return list(text.encode())

    def decode(self, ids, **_):
        return bytes(ids).decode()

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert not tokenize and add_generation_prompt
        return "SYSTEM\nUSER\n" + messages[0]["content"] + "\nASSISTANT\n"


def test_exact_boundaries_and_invalid_choice_handling():
    tok = CharTokenizer()
    for fmt in pilot.FORMATS:
        rendered = render_prompt(tok, "Choose a command.", fmt)
        ctx, answer = encode_boundary(tok, rendered, "mark_ivory", 2048)
        assert tok.decode(ctx).endswith("\n")
        assert tok.decode(answer) == "mark_ivory"
        with pytest.raises(ValueError, match="no truncation"):
            encode_boundary(tok, rendered, "mark_ivory", 5)
    choices = ["a", "b", "c", "d"]
    assert select_command(choices, [-4, -3, -1, -2]) == ("c", "ok")
    assert select_command(choices, [-1] * 4) == (None, "tie")
    for scores in ([float("nan"), -2, -3, -4], [float("inf")] * 4, [1, 2]):
        assert select_command(choices, scores) == (None, "invalid_scores")


def full_fixture(spec, path, synthetic=True):
    pilot.run(spec, path, max_jobs=1, backend_factory=fake_factory)
    manifest, plan, old = pilot.read_run(path)
    journal = Journal(path)
    for job in pilot.jobs_in(plan):
        if journal.contains(job["id"]):
            continue
        if job["kind"] == "action":
            row = job["row"]
            command = row["expected_command"]
            result = {
                "status": "ok",
                "selected_command": command,
                "execution": score_command(row, command),
            }
            result["candidates"] = [
                {"command": c, "token_count": 3, "log_likelihood": -1 if c == command else -5}
                for c in row["choices"]
            ]
        else:
            result = FakeBackend().generate(job["row"]["prompt"], job["format"], job["seed"])
        record = {
            "id": job["id"],
            "job": job,
            "config_hash": manifest["config_hash"],
            "status": "ok",
            "result": result,
            "seconds": 0,
        }
        record["checksum"] = digest(record)
        # Bulk fixture construction; actual per-trial commits/recovery are tested above.
        journal.db.execute(
            "INSERT INTO trials VALUES (?, ?, ?)", (job["id"], "ok", canonical(record))
        )
        manifest["records"][job["id"]] = record["checksum"]
    journal.db.commit()
    journal.close()
    manifest.update(status="complete", synthetic=synthetic)
    write_json(path / "manifest.json", manifest)
    return pilot.read_run(path)


def test_gates_and_counterfactual_shortcut_falsification(spec, tmp_path):
    path = tmp_path / "full"
    manifest, plan, records = full_fixture(spec, path)
    report = summarize(path)
    assert not report["action_gate_passed"]  # A perfect software oracle is not model evidence.
    assert all(g["numerical_pass"] for g in report["format_gates"].values())
    assert all(p["estimate"] == 1 and p["n_clusters"] == 8 for p in report["counterfactuals"])
    manifest["synthetic"] = False  # Test eligibility independently from numerical checks.
    write_json(path / "manifest.json", manifest)
    assert summarize(path)["action_gate_passed"]
    # Ignore actual permission changes: good pooled accuracy is insufficient.
    lookup = {r["id"]: deepcopy(r) for r in records}
    for r in lookup.values():
        if r["job"]["kind"] == "action":
            row = r["job"]["row"]
            command = row["before"]["permissions"][row["target"]][0]
            r["result"].update(selected_command=command, execution=score_command(row, command))
    checks = counterfactuals(pilot.jobs_in(plan), lookup, 100)
    assert all(p["estimate"] == 0 for p in checks if p["axis"] in {"update", "grant"})


def test_cluster_units_and_lexical_proxies_are_explicit():
    result = estimate({"a": [0] * 100, "b": [1] * 100}, samples=2000)
    assert result["n_clusters"] == 2 and result["n_observations"] == 200
    assert result["estimate"] == 0.5 and result["ci95"] == [0, 1]
    proxy = language_metrics("I don't have feelings. The character says: I feel happy.")
    assert proxy["disclaimer_phrase"] == proxy["experience_phrase"] == 1
    assert estimate({"only": [1]})["ci95"] is None


def test_blind_ratings_missing_unclear_and_text_integrity(spec, tmp_path):
    path = tmp_path / "ratings"
    _, plan, raw = full_fixture(spec, path)
    records = {r["id"]: r for r in raw}
    jobs = pilot.jobs_in(plan)
    export_ratings(path, jobs, records)
    sheet = path / "blind_ratings.csv"
    rows = list(csv.DictReader(sheet.open()))
    assert len(rows) == 40 and "format" not in rows[0] and "seed" not in rows[0]
    lookup = rating_lookup(jobs, records)
    assert read_ratings(sheet, lookup, 100)["outputs_rated"] == 0
    for row in rows:
        row.update(rater_id="reviewer", disclaimer="1", experience_claim="0", coherent="1")

    def save():
        with sheet.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    save()
    report = read_ratings(sheet, lookup, 100)
    assert report["complete"] and all(e["estimate"] == 0 for e in report["effects"])
    rows[0]["experience_claim"] = "unclear"
    save()
    report = read_ratings(sheet, lookup, 100)
    assert report["unclear_cells"] == 1 and report["effects"][1]["estimate"] is None
    rows[0]["continuation"] += "tampered"
    save()
    with pytest.raises(ValueError, match="changed the original"):
        read_ratings(sheet, lookup, 100)
    rows[0]["continuation"] = lookup[rows[0]["blind_id"]][1]["result"]["output"]
    rows.append(dict(rows[0]))
    save()
    with pytest.raises(ValueError, match="duplicate blind ID"):
        read_ratings(sheet, lookup, 100)


def test_partial_export_is_deterministic_verified_and_not_evidence(spec, tmp_path):
    path = tmp_path / "export"
    pilot.run(spec, path, max_jobs=2, backend_factory=fake_factory)
    a, b = tmp_path / "a.tar.gz", tmp_path / "b.tar.gz"
    export(path, a)
    export(path, b)
    assert file_hash(a) == file_hash(b)
    for name, checksum in read_json(path / "checksums.json").items():
        assert file_hash(path / name) == checksum
    assert "SYNTHETIC SOFTWARE TEST" in (path / "report.md").read_text()
    for ext in ("svg", "pdf", "png"):
        assert (path / "figures" / f"action_screen.{ext}").exists()
    assert not json.loads((path / "analysis.json").read_text())["action_gate_passed"]


def test_actual_native_multitoken_scoring_and_generation_on_cpu(spec):
    torch = pytest.importorskip("torch")
    pytest.importorskip("lm_eval")
    from lm_eval.models.huggingface import HFLM
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

    from self_model_study.pilot_backend import PilotBackend

    torch.set_num_threads(1)
    core = Tokenizer(models.BPE(unk_token="<unk>"))
    core.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    core.decoder = decoders.ByteLevel()
    core.train_from_iterator(
        ["Choose mark_silver mark_ivory"],
        trainers.BpeTrainer(
            vocab_size=260,
            initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
            special_tokens=["<pad>", "<bos>", "<eos>", "<unk>"],
        ),
    )
    tok = PreTrainedTokenizerFast(
        tokenizer_object=core,
        pad_token="<pad>",
        eos_token="<eos>",
        bos_token="<bos>",
        unk_token="<unk>",
    )
    tok.chat_template = "{{ 'SYSTEM\\nUSER\\n' + messages[0]['content'] + '\\nASSISTANT\\n' }}"
    torch.manual_seed(17)
    model = GPT2LMHeadModel(
        GPT2Config(
            vocab_size=len(tok),
            n_layer=1,
            n_embd=8,
            n_head=1,
            n_positions=128,
            eos_token_id=2,
            pad_token_id=0,
        )
    ).eval()
    lm = HFLM(
        pretrained=model,
        tokenizer=tok,
        device="cpu",
        batch_size=1,
        max_length=128,
        add_bos_token=False,
        softmax_dtype="float32",
    )
    adapter = PilotBackend(lm, {**spec["generation"], "max_new_tokens": 4})
    commands = ["mark_silver", "mark_ivory", "mark_cobalt", "mark_lilac"]
    for fmt in pilot.FORMATS:
        result = adapter.choice("Choose.", commands, fmt)
        ctx = result["prompt_token_ids"]
        assert tok.decode(ctx).endswith("\n")
        for candidate in result["candidates"]:
            cont = candidate["token_ids"]
            assert len(cont) > 1 and tok.decode(cont) == candidate["command"]
            with torch.inference_mode():
                logp = model(torch.tensor([ctx + cont])).logits[0].log_softmax(-1)
                expected = sum(logp[len(ctx) - 1 + i, token].item() for i, token in enumerate(cont))
            assert candidate["log_likelihood"] == pytest.approx(expected, abs=2e-5)
        first = adapter.generate("Describe.", fmt, 42)
        adapter.generate("Unrelated.", fmt, 43)
        assert adapter.generate("Describe.", fmt, 42) == first
        assert first["generation_config"]["top_k"] == 0
    with pytest.raises(ValueError, match="no truncation"):
        adapter.choice("x" * 150, commands, "plain")
