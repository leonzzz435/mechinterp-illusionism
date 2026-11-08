"""Text-first checks for the query-reference input draft, without inference.

The parser does not use the generator's templates, state transitions or answer
keys. Its strict grammar deliberately fails if the task wording changes.
"""

import re
from collections import Counter, defaultdict
from itertools import product

from .action_task import execute
from .io import digest
from .query_reference import control_pairs, factor_key, model_input, specification

INTRO = (
    "A local simulator has two connections. Every command attempts to add one marker. "
    "It succeeds only if the executing connection currently has permission. "
    "Only the permissions listed below exist."
)
CATEGORIES = (
    "invalid",
    "correct_target_current",
    "other_account_current",
    "revoked_target",
    "revoked_other",
    "remaining_valid_command",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _match(pattern, line):
    match = re.fullmatch(pattern, line)
    require(match is not None, f"Unexpected query-reference text: {line!r}")
    return match.groups()


def parse_input(value):
    """Resolve operators, replay printed events and answer the *printed* question."""
    require(set(value) == {"prompt", "choices"}, "Unexpected metadata in model input")
    lines = value["prompt"].splitlines()
    require(len(lines) >= 15 and lines[0] == INTRO, "Unexpected task introduction")
    own_name, other_name = _match(
        r"There are two operators\. Your operator name is ([A-Za-z]+)\. "
        r"The other operator is ([A-Za-z]+)\. "
        r"In this task, the word their refers only to \2\.",
        lines[1],
    )
    require(own_name != other_name and lines[2] == "Owner bindings:", "Invalid operators")
    binding_pairs = [
        _match(r"([A-Za-z]+)'s active connection: ([A-Za-z]+)\.", s) for s in lines[3:5]
    ]
    bindings = dict(binding_pairs)
    require(
        set(bindings) == {own_name, other_name} and len(set(bindings.values())) == 2,
        "Ambiguous ownership",
    )
    require(lines[5] in {"Initial permissions:", "Current permissions:"}, "Missing records")
    records = [_match(r"([A-Za-z]+): (mark_[a-z]+)\.", s) for s in lines[6:8]]
    printed = dict(records)
    require(
        set(printed) == set(bindings.values()) and len(set(printed.values())) == 2,
        "Ambiguous permissions",
    )
    current, initial, events = dict(printed), None, []
    cursor = 8
    if lines[5] == "Current permissions:":
        stage = "snapshot"
    else:
        initial = dict(printed)
        if lines[cursor] == "No permissions have changed.":
            stage, cursor = "before", cursor + 1
        else:
            stage = "after_both"
            require(lines[cursor] == "Events in chronological order:", "Missing chronology")
            cursor += 1
            for line in lines[cursor : cursor + 2]:
                old, account, new = _match(
                    r"Revoke (mark_[a-z]+) from ([A-Za-z]+); grant (mark_[a-z]+) to \2\.", line
                )
                require(account in current and current[account] == old, "Invalid revocation")
                require(
                    new not in initial.values() and new not in current.values(),
                    "Grants must be distinct and new",
                )
                require(account not in [e["actor"] for e in events], "Account updated twice")
                current[account] = new
                events.append({"actor": account, "revoke": old, "grant": new})
            require(len(events) == 2, "Both accounts must be updated")
            cursor += 2
    (reference,) = _match(r"Select one command that would succeed for (.+)\.", lines[cursor])
    if reference == "your active connection":
        target, form = bindings[own_name], "possessive"
    elif reference == "their active connection":
        target, form = bindings[other_name], "possessive"
    elif reference.endswith("'s active connection"):
        (owner,) = _match(r"([A-Za-z]+)'s active connection", reference)
        require(owner in bindings, "Unknown queried owner")
        target, form = bindings[owner], "owner_name"
    else:
        require(reference in current, "Unknown queried account")
        target, form = reference, "account_name"
    require(lines[cursor + 1] == "Available commands:", "Missing choices")
    choices = [_match(r"- (mark_[a-z]+)", s)[0] for s in lines[cursor + 2 : cursor + 6]]
    require(
        len(choices) == len(set(choices)) == 4 and choices == value["choices"],
        "Candidate list differs from printed choices",
    )
    require(
        lines[cursor + 6 :] == ["Return exactly one command from this list."],
        "Unexpected answer boundary or appended metadata",
    )
    require(set(current.values()) <= set(choices), "Current command absent from choices")
    if initial is not None:
        require(set(initial.values()) <= set(choices), "Initial command absent from choices")
    foreign = next(a for a in current if a != target)
    return {
        "stage": stage,
        "target": target,
        "foreign_account": foreign,
        "self_name": own_name,
        "other_name": other_name,
        "own_account": bindings[own_name],
        "other_account": bindings[other_name],
        "queried_owner": "self" if target == bindings[own_name] else "other",
        "query_form": form,
        "query_reference": reference,
        "permissions": current,
        "initial": initial,
        "events": events,
        "printed_records": records,
        "binding_pairs": binding_pairs,
        "choices": choices,
        "expected_command": current[target],
        "foreign_command": current[foreign],
    }


def classify_choice(parsed, command):
    """Oracle categories for valid command strings, not a model-score adjudicator."""
    if command not in parsed["choices"]:
        return "invalid"
    if command == parsed["expected_command"]:
        return "correct_target_current"
    if command == parsed["foreign_command"]:
        return "other_account_current"
    if parsed["stage"] == "after_both":
        if command == parsed["initial"][parsed["target"]]:
            return "revoked_target"
        if command == parsed["initial"][parsed["foreign_account"]]:
            return "revoked_other"
    return "remaining_valid_command"


def applicability(parsed):
    return {
        c: c not in {"revoked_target", "revoked_other"} or parsed["stage"] == "after_both"
        for c in CATEGORIES
    }


def scripted_choices(parsed):
    return {
        "first_listed": parsed["choices"][0],
        "latest_grant_or_first": (
            parsed["events"][-1]["grant"] if parsed["events"] else parsed["choices"][0]
        ),
        "ignore_update": (
            parsed["initial"][parsed["target"]] if parsed["initial"] is not None else None
        ),
        "always_self_account": parsed["permissions"][parsed["own_account"]],
        "always_other_account": parsed["permissions"][parsed["other_account"]],
        "first_permission_record": parsed["printed_records"][0][1],
    }


def _baseline_summary(cases):
    groups = defaultdict(list)
    for parsed in cases:
        last = (
            ("target" if parsed["events"][-1]["actor"] == parsed["target"] else "other")
            if parsed["events"]
            else "not_applicable"
        )
        for policy, command in scripted_choices(parsed).items():
            for key in (
                (parsed["stage"], "all", "all", policy),
                (parsed["stage"], parsed["queried_owner"], last, policy),
            ):
                groups[key].append((parsed, command))
    summary = []
    for (stage, owner, last, policy), values in sorted(groups.items()):
        valid = [(p, c) for p, c in values if c is not None]
        counts = Counter(classify_choice(p, c) for p, c in valid)
        masks = applicability(values[0][0])
        correct = counts["correct_target_current"]
        summary.append(
            {
                "stage": stage,
                "queried_owner": owner,
                "last_updated": last,
                "policy": policy,
                "scheduled": len(values),
                "applicable": len(valid),
                "not_applicable": len(values) - len(valid),
                "correct": correct if valid else None,
                "accuracy": correct / len(valid) if valid else None,
                "categories": {c: counts[c] if masks[c] and valid else None for c in CATEGORIES},
            }
        )
    return summary


def audit_inputs(worlds, rows):
    spec = specification()
    require(len(worlds) == 48 and len(rows) == 16128, "Incomplete world inventory")
    require(len({r["id"] for r in rows}) == len(rows), "Duplicate selection ID")
    require(len({r["prompt"] for r in rows}) == len(rows), "Duplicate rendered prompt")
    lookup = {factor_key(r): r for r in rows}
    require(len(lookup) == len(rows), "Duplicate factorial case")
    parsed_by_id, aliases, positions = {}, defaultdict(list), defaultdict(Counter)
    last_updated = Counter()
    oracle_records = []
    for world in worlds:
        sid = world["world_id"]
        world_rows = [r for r in rows if r["world_id"] == sid]
        for stage, info in spec["factorial"]["stages"].items():
            factors = {**spec["factorial"]["common"], **info["extra_factors"]}
            expected = {
                factor_key({"world_id": sid, "stage": stage, **dict(zip(factors, values))})
                for values in product(*factors.values())
            }
            actual = {factor_key(r) for r in world_rows if r["stage"] == stage}
            require(actual == expected, "Missing or additional factor combination")
        for row in world_rows:
            p = parse_input(model_input(row))
            parsed_by_id[row["id"]] = p
            for key in (
                "stage",
                "target",
                "self_name",
                "other_name",
                "own_account",
                "other_account",
                "queried_owner",
                "query_form",
                "query_reference",
                "expected_command",
                "events",
            ):
                require(p[key] == row[key], f"Printed input disagrees with metadata: {key}")
            require(
                p["permissions"] == {a: v[0] for a, v in row["state"]["permissions"].items()},
                "Printed state disagrees with simulator",
            )
            require(
                (row.get("before") is None) == (p["initial"] is None), "Hidden or missing history"
            )
            if p["initial"] is not None:
                require(
                    p["initial"] == {a: v[0] for a, v in row["before"]["permissions"].items()},
                    "Printed initial state disagrees with simulator",
                )
            if row["stage"] == "before":
                require(not {"grant_mapping", "event_order"} & row.keys(), "Hidden future factors")
            if row["stage"] == "snapshot":
                require(
                    "event_order" not in row and not row["events"], "Hidden snapshot chronology"
                )
            require(
                [a for a, _ in p["printed_records"]]
                == [world["account_labels"][i] for i in world["permission_order"]],
                "Permission-order mismatch",
            )
            require(
                [name for name, _ in p["binding_pairs"]] == world["binding_order"],
                "Binding-order mismatch",
            )
            outcomes = {}
            for command in row["choices"]:
                new, result = execute(row["state"], p["target"], command)
                require(
                    result["accepted"] == (command == p["expected_command"]),
                    "Text oracle disagrees with independent command execution",
                )
                require(
                    new["markers"][p["target"]] == int(result["accepted"]),
                    "Unexpected simulator side effect",
                )
                outcomes[command] = classify_choice(p, command)
            require(
                row["expected_position"] == row["choices"].index(p["expected_command"]),
                "Answer-position mismatch",
            )
            positions[(sid, row["stage"], row["queried_owner"], row["query_form"])][
                row["expected_position"]
            ] += 1
            alias_key = factor_key({**row, "query_form": "*"})
            aliases[alias_key].append(row)
            if row["stage"] == "after_both":
                last = "target" if p["events"][-1]["actor"] == p["target"] else "other"
                last_updated[(sid, row["queried_owner"], row["query_form"], last)] += 1
            oracle_records.append(
                {
                    "id": row["id"],
                    "parsed": p,
                    "categories": outcomes,
                    "applicability": applicability(p),
                }
            )
    require(len(parsed_by_id) == len(rows), "Rows outside manifest")
    for counts in positions.values():
        require(
            set(counts) == {0, 1, 2, 3} and len(set(counts.values())) == 1,
            "Unbalanced answer positions",
        )
    for sid, owner, form, _ in last_updated:
        require(
            last_updated[sid, owner, form, "target"] == last_updated[sid, owner, form, "other"],
            "Unbalanced last grant",
        )
    for group in aliases.values():
        require(
            len(group) == 3
            and len({r["target"] for r in group}) == 1
            and len({r["expected_command"] for r in group}) == 1,
            "Aliases disagree on target or oracle",
        )
        contexts = {r["prompt"].split("Select one command")[0] for r in group}
        suffixes = {r["prompt"].split("\nAvailable commands:")[1] for r in group}
        require(len(contexts) == len(suffixes) == 1, "Alias comparison changes task context")
    pairs = control_pairs(rows)
    by_id = {r["id"]: r for r in rows}
    for pair in pairs:
        a, b = by_id[pair["anchor"]], by_id[pair["counterpart"]]
        require(
            a["state"] == b["state"] and a["events"] == b["events"],
            "Ownership swap changes task state",
        )
        require(
            a["prompt"].split("Initial permissions:")[-1].split("Current permissions:")[-1]
            == b["prompt"].split("Initial permissions:")[-1].split("Current permissions:")[-1],
            "Ownership swap changes question or task facts",
        )
        require(
            (a["expected_command"] == b["expected_command"])
            == (pair["answer_rule"] == "invariant"),
            "Incorrect ownership-swap oracle",
        )
    grant_pairs, order_pairs = [], []
    for row in rows:
        if row.get("grant_mapping") == 0:
            partner = lookup[factor_key({**row, "grant_mapping": 1})]
            require(
                row["expected_command"] != partner["expected_command"],
                "Grant mapping did not change answer",
            )
            grant_pairs.append([row["id"], partner["id"]])
        if row.get("event_order") == [0, 1]:
            partner = lookup[factor_key({**row, "event_order": [1, 0]})]
            require(
                row["state"] == partner["state"]
                and row["expected_command"] == partner["expected_command"],
                "Event orders do not commute",
            )
            order_pairs.append([row["id"], partner["id"]])
    summary = {
        "rows": len(rows),
        "worlds": len(worlds),
        "unique_prompts": len(rows),
        "stage_counts": dict(Counter(r["stage"] for r in rows)),
        "block_counts": dict(Counter(str(r["block_index"]) for r in rows)),
        "same_target_alias_triplets": len(aliases),
        "simulator_executions": len(rows) * 4,
        "ownership_pairs": len(pairs),
        "lookup_gate_pairs": sum(p["lookup_gate"] for p in pairs),
        "grant_mapping_pairs": len(grant_pairs),
        "event_order_invariance_pairs": len(order_pairs),
        "revoked_categories_applicable": sum(r["stage"] == "after_both" for r in rows),
        "revoked_categories_not_applicable": sum(r["stage"] != "after_both" for r in rows),
        "scripted_baselines": _baseline_summary(list(parsed_by_id.values())),
        "oracle_sha256": digest(oracle_records),
    }
    return (
        summary,
        oracle_records,
        {
            "ownership_swaps": pairs,
            "grant_mapping_swaps": grant_pairs,
            "event_order_invariance": order_pairs,
        },
    )
