"""CPU checks of printed semantics, controls, freshness and archived token inputs."""

import gzip
import importlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from self_model_study.io import digest
from self_model_study.query_reference import (
    build_inputs,
    control_pairs,
    factor_key,
    fingerprint,
    model_input,
)
from self_model_study.query_reference_audit import (
    applicability,
    audit_inputs,
    classify_choice,
    parse_input,
    scripted_choices,
)


@pytest.fixture(scope="module")
def inputs():
    return build_inputs()


@pytest.fixture(scope="module")
def audited(inputs):
    return audit_inputs(*inputs)


@pytest.fixture
def preparation(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("prepare_query_reference")


def pick(rows, **factors):
    return next(r for r in rows if all(r.get(k) == v for k, v in factors.items()))


def test_complete_balanced_inventory_matches_reviewed_world_assignment(inputs, audited):
    worlds, rows = inputs
    prior = json.loads(Path("review/query-self-reference-protocol-check.json").read_text())
    assignment = {
        "worlds": {
            w["world_id"]: {
                k: w[k] for k in ("account_labels", "operator_labels", "command_labels")
            }
            for w in worlds
        },
        "nuisance": {w["world_id"]: w["nuisance"] for w in worlds},
    }
    assert digest(assignment) == prior["world_assignment_hash"]
    assert Counter(w["self_name"] for w in worlds) == {"Rowan": 24, "Morgan": 24}
    assert Counter(w["nuisance"] for w in worlds) == {i: 6 for i in range(8)}
    summary, oracles, pairs = audited
    assert summary["stage_counts"] == {"before": 2304, "snapshot": 4608, "after_both": 9216}
    assert summary["block_counts"] == {str(i): 2688 for i in range(6)}
    assert summary["same_target_alias_triplets"] == 5376
    assert summary["lookup_gate_pairs"] == 2304
    assert len(oracles) == len(rows) == 16128
    assert len(pairs["grant_mapping_swaps"]) == 6912
    assert len(pairs["event_order_invariance"]) == 4608
    assert digest(build_inputs()) == digest(inputs)


def test_complete_input_boundary_and_no_invisible_future_variants(inputs):
    _, rows = inputs
    for row in rows:
        value = model_input(row)
        assert set(value) == {"prompt", "choices"}
        assert row["id"] not in value["prompt"] and row["world_id"] not in value["prompt"]
        if row["stage"] == "before":
            assert "event_order" not in row and "grant_mapping" not in row
            assert not row["events"]
        if row["stage"] == "snapshot":
            assert "before" not in row and "event_order" not in row and not row["events"]
    row = rows[0]
    leaked = {**model_input(row), "answer": row["expected_command"]}
    with pytest.raises(ValueError, match="metadata"):
        parse_input(leaked)
    value = model_input(row)
    value["choices"].clear()
    assert len(row["choices"]) == 4


def test_text_oracle_resolves_both_operators_and_replays_events_independently(inputs):
    worlds, rows = inputs
    for name in ("Rowan", "Morgan"):
        w = next(w for w in worlds if w["self_name"] == name)
        for assignment in (0, 1):
            for owner in ("self", "other"):
                for form in ("possessive", "owner_name", "account_name"):
                    row = pick(
                        rows,
                        world_id=w["world_id"],
                        connection_assignment=assignment,
                        queried_owner=owner,
                        query_form=form,
                        stage="after_both",
                        grant_mapping=0,
                    )
                    parsed = parse_input(model_input(row))
                    target_index = assignment if owner == "self" else 1 - assignment
                    assert parsed["target"] == w["account_labels"][target_index]
                    assert parsed["expected_command"] == w["commands"][2 + target_index]
                    assert parsed["foreign_command"] == w["commands"][3 - target_index]


@pytest.mark.parametrize("mutation", ["binding", "question", "event", "oracle", "factor"])
def test_audit_rejects_text_or_metadata_corruption(inputs, mutation):
    worlds, rows = inputs
    original = pick(rows, stage="after_both", query_form="possessive", queried_owner="self")
    changed = deepcopy(original)
    if mutation == "binding":
        a, b = changed["own_account"], changed["other_account"]
        changed["prompt"] = changed["prompt"].replace(
            f"active connection: {a}.", f"active connection: {b}.", 1
        )
    elif mutation == "question":
        changed["prompt"] = changed["prompt"].replace(
            "succeed for your active connection", "succeed for their active connection"
        )
    elif mutation == "event":
        old = changed["events"][0]["revoke"]
        changed["prompt"] = changed["prompt"].replace("Revoke " + old, "Revoke mark_unknown")
    elif mutation == "oracle":
        changed["expected_command"] = changed["before"]["permissions"][changed["target"]][0]
    else:
        changed["grant_mapping"] = 1 - changed["grant_mapping"]
    broken = [changed if r is original else r for r in rows]
    with pytest.raises(ValueError):
        audit_inputs(worlds, broken)


def test_incomplete_inventory_cannot_be_audited(inputs):
    worlds, rows = inputs
    with pytest.raises(ValueError, match="inventory"):
        audit_inputs(worlds, rows[:-1])


def test_ownership_pairs_hold_question_fixed_but_not_always_owner_label(inputs):
    _, rows = inputs
    by_id = {r["id"]: r for r in rows}
    pairs = control_pairs(rows)
    assert len({p["anchor"] for p in pairs}) == len(pairs) == 8064
    gate_cells = Counter()
    for pair in pairs:
        a, b = by_id[pair["anchor"]], by_id[pair["counterpart"]]
        assert a["connection_assignment"] == 0 and b["connection_assignment"] == 1
        assert a["query_reference"] == b["query_reference"]
        assert a["state"] == b["state"] and a["choices"] == b["choices"]
        if a["query_form"] == "account_name":
            assert a["queried_owner"] != b["queried_owner"]
            assert a["target"] == b["target"] and a["expected_command"] == b["expected_command"]
        else:
            assert a["queried_owner"] == b["queried_owner"]
            assert a["target"] != b["target"] and a["expected_command"] != b["expected_command"]
        if pair["lookup_gate"]:
            gate_cells[pair["stage"], pair["anchor_owner"], pair["query_form"]] += 1
    assert len(gate_cells) == 8
    assert set(gate_cells.values()) == {192, 384}


def test_snapshot_revocations_are_inapplicable_not_zero_observations(inputs, audited):
    _, rows = inputs
    for stage in ("before", "snapshot", "after_both"):
        row = pick(rows, stage=stage)
        p = parse_input(model_input(row))
        categories = [classify_choice(p, c) for c in row["choices"]]
        assert categories.count("correct_target_current") == 1
        assert categories.count("other_account_current") == 1
        assert applicability(p)["revoked_target"] == (stage == "after_both")
        assert applicability(p)["revoked_other"] == (stage == "after_both")
        if stage == "after_both":
            assert categories.count("revoked_target") == categories.count("revoked_other") == 1
        else:
            assert categories.count("remaining_valid_command") == 2
        assert classify_choice(p, "unknown") == "invalid"
        assert classify_choice(p, None) == "invalid"
    for cell in audited[0]["scripted_baselines"]:
        if cell["stage"] != "after_both":
            assert cell["categories"]["revoked_target"] is None
            assert cell["categories"]["revoked_other"] is None


def test_shortcuts_expose_latest_grant_confound_and_snapshot_inapplicability(inputs, audited):
    _, rows = inputs
    totals = {
        (r["stage"], r["policy"]): r
        for r in audited[0]["scripted_baselines"]
        if r["queried_owner"] == "all"
    }
    assert totals["after_both", "latest_grant_or_first"]["accuracy"] == 0.5
    assert totals["after_both", "ignore_update"]["accuracy"] == 0
    assert totals["before", "ignore_update"]["accuracy"] == 1
    assert totals["snapshot", "ignore_update"]["accuracy"] is None
    assert totals["snapshot", "ignore_update"]["not_applicable"] == 4608
    for stage in ("before", "snapshot", "after_both"):
        assert totals[stage, "first_listed"]["accuracy"] == 0.25
    for cell in audited[0]["scripted_baselines"]:
        if cell["policy"] == "latest_grant_or_first" and cell["stage"] == "after_both":
            if cell["last_updated"] != "all":
                assert cell["accuracy"] == (1 if cell["last_updated"] == "target" else 0)
    row = pick(rows, stage="snapshot")
    assert scripted_choices(parse_input(model_input(row)))["ignore_update"] is None


def test_event_order_commutes_and_grant_mapping_changes_answers(inputs):
    _, rows = inputs
    lookup = {factor_key(r): r for r in rows}
    a = pick(rows, stage="after_both", event_order=[0, 1], grant_mapping=0)
    b = lookup[factor_key({**a, "event_order": [1, 0]})]
    c = lookup[factor_key({**a, "grant_mapping": 1})]
    assert a["prompt"] != b["prompt"] and a["state"] == b["state"]
    assert a["expected_command"] == b["expected_command"] != c["expected_command"]
    assert a["events"][-1]["actor"] != b["events"][-1]["actor"]


def test_freshness_rejects_exact_context_stripped_and_fingerprint_reuse(inputs, preparation):
    worlds, rows = inputs
    row, world = rows[0], worlds[0]
    for kind in ("exact", "stripped", "fingerprint"):
        exact, stripped, fingerprints = set(), set(), set()
        if kind == "exact":
            exact.add(digest(row["prompt"]))
        elif kind == "stripped":
            altered_context = "A different ownership introduction.\n" + preparation.task_body(
                row["prompt"]
            )
            assert altered_context != row["prompt"]
            stripped.add(digest(preparation.task_body(altered_context)))
        else:
            fingerprints.add(fingerprint(world["account_labels"][::-1], world["commands"][::-1]))
        with pytest.raises(ValueError, match="Historical"):
            preparation.check_freshness(worlds, rows, (exact, stripped, fingerprints, {}))


def test_history_audit_fails_closed_without_archives(tmp_path, preparation):
    with pytest.raises(ValueError, match="Missing historical"):
        preparation.historical_inventory(tmp_path)


class CharacterTokenizer:
    chat_template = "fixture"

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert not tokenize and add_generation_prompt and len(messages) == 1
        return messages[0]["content"] + "\nAssistant:\n"

    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens
        return list(text.encode())

    def decode(self, ids):
        return bytes(ids).decode()

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": self.encode(text, add_special_tokens)}


def test_token_boundary_archive_contains_exact_commands_and_no_eos(inputs, preparation):
    row = inputs[1][0]
    tokenizer = CharacterTokenizer()
    encoded = next(preparation.token_records([row], tokenizer))
    for candidate in encoded["candidates"]:
        assert tokenizer.decode(candidate["token_ids"]) == candidate["command"]
        assert candidate["total_tokens"] == encoded["prompt_token_count"] + candidate["token_count"]
        assert encoded["prompt_token_ids"] + candidate["token_ids"] == tokenizer.encode(
            encoded["rendered_prompt"] + candidate["command"]
        )


@pytest.mark.parametrize("failure", ["merge", "decode", "overflow", "independent_encoding"])
def test_token_audit_rejects_boundary_decode_overflow_or_encoding_failure(
    inputs, preparation, failure
):
    row = deepcopy(inputs[1][0])

    class BrokenTokenizer(CharacterTokenizer):
        def encode(self, text, add_special_tokens=False):
            ids = super().encode(text, add_special_tokens)
            if failure == "merge" and text.endswith(tuple(row["choices"])):
                ids[0] += 1
            return ids

        def decode(self, ids):
            return "bad decode" if failure == "decode" else super().decode(ids)

        def __call__(self, text, add_special_tokens=False):
            value = super().__call__(text, add_special_tokens)
            if failure == "independent_encoding":
                value["input_ids"].append(999)
            return value

    if failure == "overflow":
        row["prompt"] += "x" * 2048
    with pytest.raises(ValueError):
        list(preparation.token_records([row], BrokenTokenizer()))


def test_reproducible_archive_and_existing_evidence_is_never_overwritten(tmp_path, preparation):
    staging = tmp_path / "staging"
    staging.mkdir()
    first = staging / "input.jsonl.gz"
    preparation._jsonl_gz(first, [{"a": 1}, {"b": 2}])
    expected = first.read_bytes()
    assert [json.loads(s) for s in gzip.decompress(expected).splitlines()] == [{"a": 1}, {"b": 2}]
    destination = tmp_path / "saved"
    assert preparation.publish_artifacts(staging, destination) == "created"
    staging.mkdir()
    preparation._jsonl_gz(first, [{"a": 1}, {"b": 2}])
    assert first.read_bytes() == expected
    assert preparation.publish_artifacts(staging, destination) == "verified_identical"
    first.write_bytes(b"altered")
    with pytest.raises(ValueError, match="differs"):
        preparation.publish_artifacts(staging, destination)
    assert (destination / first.name).read_bytes() == expected
