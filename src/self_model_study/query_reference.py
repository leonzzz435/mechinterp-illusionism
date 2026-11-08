"""CPU-only inputs for query-self-reference-v1; no model or execution engine.

The scientific JSON remains a review draft. Audit labels and simulator state are
kept outside the two-field model input returned by ``model_input``.
"""

from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path

from .action_task import apply_update, successful_commands
from .io import digest, file_hash, read_json

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "designs/query-self-reference-v1.json"
SPEC_SHA256 = "6c1891acedcf758cb5ce099b001ba609c5627a484ccaf873f1f9019c5b3e81cc"
PROTOCOL = "query-self-reference-v1"


def specification():
    if file_hash(SPEC_PATH) != SPEC_SHA256:
        raise ValueError("Query-reference draft changed; review and re-audit before proceeding")
    return read_json(SPEC_PATH)


def world_manifest():
    sample = specification()["sampling"]
    ids = [f"query-self-v1:{i:04d}" for i in range(sample["world_count"])]
    ranked = sorted(ids, key=lambda sid: digest([sample["seed"], "nuisance", sid]))
    nuisance = {sid: rank % 8 for rank, sid in enumerate(ranked)}
    worlds = []
    for index, sid in enumerate(ids):
        labels = {
            pool: sorted(
                sample[pool], key=lambda label: digest([sample["seed"], sid, pool, label])
            )[:count]
            for pool, count in (("account_labels", 2), ("command_labels", 4))
        }
        operators = sample["operator_labels"]
        bits = nuisance[sid]
        worlds.append(
            {
                "world_id": sid,
                "world_index": index,
                "block_index": index // 8,
                **labels,
                "operator_labels": list(operators),
                "commands": [f"mark_{label}" for label in labels["command_labels"]],
                "nuisance": bits,
                "permission_order": [1, 0] if bits & 1 else [0, 1],
                # Base binding order is the declared operator_labels order, not own/other.
                "binding_order": list(reversed(operators)) if bits & 2 else list(operators),
                "self_name": operators[(bits >> 2) & 1],
                "other_name": operators[1 - ((bits >> 2) & 1)],
            }
        )
    fingerprints = [fingerprint(w["account_labels"], w["commands"]) for w in worlds]
    if len(set(fingerprints)) != len(worlds):
        raise ValueError("Repeated account/command set; no silent resampling")
    if Counter(w["nuisance"] for w in worlds) != {i: 6 for i in range(8)}:
        raise ValueError("Unbalanced world nuisances")
    return worlds


def fingerprint(accounts, commands):
    return digest([sorted(accounts), sorted(commands)])


def factor_key(row):
    return (
        row["world_id"],
        row["stage"],
        row["connection_assignment"],
        row["queried_owner"],
        row["query_form"],
        row["option_rotation"],
        row.get("grant_mapping"),
        tuple(row["event_order"]) if "event_order" in row else None,
    )


def _row(world, stage, factors, templates):
    accounts, commands = world["account_labels"], world["commands"]
    own = accounts[factors["connection_assignment"]]
    other = accounts[1 - factors["connection_assignment"]]
    bindings = {world["self_name"]: own, world["other_name"]: other}
    target = own if factors["queried_owner"] == "self" else other
    owner = world[factors["queried_owner"] + "_name"]
    before = {
        "commands": list(commands),
        "permissions": {a: [commands[i]] for i, a in enumerate(accounts)},
        "markers": dict.fromkeys(accounts, 0),
    }
    state, events = deepcopy(before), []
    if stage != "before":
        grants = commands[2:] if factors["grant_mapping"] == 0 else commands[2:][::-1]
        updates = [
            {"actor": a, "revoke": commands[i], "grant": grants[i]} for i, a in enumerate(accounts)
        ]
        for i in factors.get("event_order", [0, 1]):
            state = apply_update(state, updates[i])
            if stage == "after_both":
                events.append(updates[i])
    rotation = factors["option_rotation"]
    choices = commands[rotation:] + commands[:rotation]
    alias = factors["query_form"]
    reference = templates["query_references"][
        factors["queried_owner"] + "_possessive" if alias == "possessive" else alias
    ].format(queried_owner_name=owner, queried_account=target)

    def permissions(s):
        return "\n".join(
            templates["permission_line"].format(
                account=accounts[i], command=s["permissions"][accounts[i]][0]
            )
            for i in world["permission_order"]
        )

    intro = templates["common_intro"].format(
        self_name=world["self_name"],
        other_name=world["other_name"],
        owner_bindings="\n".join(
            templates["binding_line"].format(owner_name=name, account=bindings[name])
            for name in world["binding_order"]
        ),
    )
    body = templates[stage + "_body"].format(
        initial_permissions=permissions(before),
        current_permissions=permissions(state),
        events="\n".join(
            templates["event_line"].format(old=e["revoke"], new=e["grant"], account=e["actor"])
            for e in events
        ),
    )
    prompt = (
        intro
        + body
        + templates["question"].format(
            query_reference=reference,
            options="\n".join(templates["option_line"].format(command=c) for c in choices),
        )
    )
    correct = successful_commands(state, target)
    if len(correct) != 1:
        raise ValueError("Ambiguous simulator oracle")
    row = {
        "world_id": world["world_id"],
        "world_index": world["world_index"],
        "block_index": world["block_index"],
        "stage": stage,
        **factors,
        "self_name": world["self_name"],
        "other_name": world["other_name"],
        "own_account": own,
        "other_account": other,
        "target": target,
        "query_reference": reference,
        "state": state,
        "events": events,
        "prompt": prompt,
        "choices": choices,
        "expected_command": correct[0],
        "expected_position": choices.index(correct[0]),
    }
    # Snapshot has no hidden initial/history record. Before has no future factors.
    if stage != "snapshot":
        row["before"] = before
    row["id"] = digest([PROTOCOL, factor_key(row)])
    return row


def build_inputs():
    spec = specification()
    worlds, rows = world_manifest(), []
    common = spec["factorial"]["common"]
    for world in worlds:
        for stage, info in spec["factorial"]["stages"].items():
            factors = {**common, **info["extra_factors"]}
            for values in product(*factors.values()):
                rows.append(_row(world, stage, dict(zip(factors, values)), spec["prompts"]))
    if len(rows) != spec["factorial"]["total_choices"]:
        raise ValueError("Incomplete query-reference inventory")
    return worlds, rows


def model_input(row):
    """The complete allowed model boundary; no label/state/ID is passed through."""
    return {"prompt": row["prompt"], "choices": list(row["choices"])}


def control_pairs(rows):
    """Each ownership swap once; account-name swaps change queried_owner metadata."""
    lookup = {factor_key(row): row for row in rows}
    if len(lookup) != len(rows):
        raise ValueError("Duplicate factor key")
    pairs = []
    for row in rows:
        if row["connection_assignment"] != 0:
            continue
        counter = {**row, "connection_assignment": 1}
        invariant = row["query_form"] == "account_name"
        if invariant:
            counter["queried_owner"] = "other" if row["queried_owner"] == "self" else "self"
        try:
            partner = lookup[factor_key(counter)]
        except KeyError as exc:
            raise ValueError("Missing ownership-swap counterpart") from exc
        pairs.append(
            {
                "anchor": row["id"],
                "counterpart": partner["id"],
                "anchor_owner": row["queried_owner"],
                "stage": row["stage"],
                "query_form": row["query_form"],
                "answer_rule": "invariant" if invariant else "changes",
                "lookup_gate": row["stage"] in {"before", "snapshot"}
                and row["query_form"] != "possessive",
            }
        )
    return pairs
