"""CPU-only task design: contextual action permissions, not model evidence.

The executor binds commands to an actor; model output cannot choose that actor.
The old datasets, scoring paths and confirmation gates remain separate.
"""

from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path

from .data import rng_for
from .io import canonical, digest, file_hash, source_hash, write_json

VERSION = "action-permissions-v2.1-draft"
VIEWS = ("self", "named_self", "other")
NAMES = ("Aster", "Birch", "Cedar", "Dune", "Elm", "Flint", "Grove", "Heath")
TOOLS = ("amber", "cobalt", "ivory", "jade", "lilac", "ochre", "silver", "violet")


def execute(state, actor, command):
    """Execute on an isolated state copy, retaining invalid/rejected commands."""
    if actor not in state["permissions"]:
        raise ValueError("Unknown executor actor")
    result = deepcopy(state)
    known = isinstance(command, str) and command in state["commands"]
    accepted = known and command in state["permissions"][actor]
    if accepted:
        result["markers"][actor] += 1
    return result, {
        "actor": actor,
        "command": command,
        "valid_command": known,
        "accepted": accepted,
        "reason": "executed" if accepted else "permission_denied" if known else "invalid_command",
    }


def apply_update(state, event):
    """A permission replacement is an actual simulator state transition."""
    actor, old, new = event["actor"], event["revoke"], event["grant"]
    if actor not in state["permissions"] or state["permissions"][actor] != [old]:
        raise ValueError("Update does not match the actor's current permission")
    if new not in state["commands"] or old == new:
        raise ValueError("Update must grant a different known command")
    result = deepcopy(state)
    result["permissions"][actor] = [new]
    return result


def successful_commands(state, actor):
    return [c for c in state["commands"] if execute(state, actor, c)[1]["accepted"]]


def render(row):
    before, event = row["before"], row["event"]
    target = "your active connection" if row["view"] == "self" else row["target"]
    history = "\n".join(
        f"{actor}: {', '.join(before['permissions'][actor])}." for actor in row["actor_order"]
    )
    update = (
        f"Revoke {event['revoke']} from {event['actor']}; "
        f"grant {event['grant']} to {event['actor']}."
        if row["phase"] == "after"
        else "The initial checkpoint is still current. No permissions have changed."
    )
    context = (
        "A local simulator has two connections. Every command attempts to add one marker. "
        "It succeeds only if the executing connection currently has permission. "
        "Only the permissions listed below exist.\n"
        f"Your active connection: {row['assigned']}.\n"
        f"Initial permissions:\n{history}\nLatest event:\n{update}\n"
    )
    prompt = (
        context
        + f"Select one command that would succeed for {target}.\nAvailable commands:\n"
        + "\n".join(f"- {c}" for c in row["choices"])
        + "\nReturn exactly one command from this list."
    )
    # Independent probe, not conditioned on a sampled action or its outcome.
    language_prompt = (
        context + f"In one or two sentences, describe the next successful action for {target}."
    )
    return prompt, language_prompt


def build_design(seed=1729, scenarios=40, split="development"):
    if split != "development":
        raise ValueError("This draft exposes development only; held-out design is not frozen")
    if type(seed) is not int or type(scenarios) is not int or not 1 <= scenarios <= 40:
        raise ValueError("Use an integer seed and 1–40 development scenarios")
    rows = []
    for index in range(scenarios):
        sid = f"{VERSION}:{seed}:development:{index:04d}"
        rng = rng_for(sid)
        actors = rng.sample(NAMES, 2)
        commands = [f"mark_{name}" for name in rng.sample(TOOLS, 4)]
        before = {
            "commands": commands,
            "permissions": {actors[0]: [commands[0]], actors[1]: [commands[1]]},
            "markers": dict.fromkeys(actors, 0),
        }
        actor_order = rng.sample(actors, 2)
        for updated, grant_variant, identity, view, phase, rotation in product(
            range(2), range(2), range(2), VIEWS, ("before", "after"), range(4)
        ):
            assigned = actors[identity]
            target = actors[1 - identity] if view == "other" else assigned
            event = {
                "actor": actors[updated],
                "revoke": commands[updated],
                "grant": commands[2 + grant_variant],
            }
            state = apply_update(before, event) if phase == "after" else deepcopy(before)
            choices = commands[rotation:] + commands[:rotation]
            successes = successful_commands(state, target)
            if len(successes) != 1:
                raise ValueError("Design requires exactly one executable command")
            row = {
                "id": digest([sid, updated, grant_variant, identity, view, phase, rotation]),
                "scenario_id": sid,
                "split": split,
                "view": view,
                "phase": phase,
                "identity": identity,
                "updated": updated,
                "grant_variant": grant_variant,
                "rotation": rotation,
                "assigned": assigned,
                "target": target,
                "actor_order": actor_order,
                "event": event,
                "before": deepcopy(before),
                "state": state,
                "choices": choices,
                "expected_command": successes[0],
                "expected_position": choices.index(successes[0]),
                "relevant_update": target == event["actor"],
                "execution_mode": "counterfactual_copy" if view == "other" else "active_copy",
            }
            row["prompt"], row["language_prompt"] = render(row)
            rows.append(row)
    return rows


def model_input(row):
    """Export text/choices separately from gold answers and structured audit metadata."""
    return {key: row[key] for key in ("id", "prompt", "choices", "language_prompt")}


def score_command(row, command):
    """Score a selected command, not an A/B/C/D token or a parsed explanation."""
    state, receipt = execute(row["state"], row["target"], command)
    return {**receipt, "correct": receipt["accepted"], "state_after": state}


def design_summary(rows):
    """Simulator/shortcut checks only. None is a measured LLM baseline."""
    positions = Counter(r["expected_position"] for r in rows)
    heuristics = {
        "first_listed": lambda r: r["choices"][0],
        "alphabetically_first": lambda r: min(r["choices"]),
        "ignore_update": lambda r: r["before"]["permissions"][r["target"]][0],
        "always_active_actor": lambda r: r["state"]["permissions"][r["assigned"]][0],
        "latest_grant_or_first": lambda r: (
            r["event"]["grant"] if r["phase"] == "after" else r["choices"][0]
        ),
        # Reviewer-discovered shortcut: use the opposite list position without
        # reading the granted command. The grant counterfactual must defeat it.
        "opposite_initial_if_updated": lambda r: r["choices"][
            (
                r["choices"].index(r["before"]["permissions"][r["target"]][0])
                + (2 if r["phase"] == "after" and r["relevant_update"] else 0)
            )
            % len(r["choices"])
        ],
    }
    by_view, changed_by_view, irrelevant_by_view = {}, {}, {}
    for view in VIEWS:
        subset = [r for r in rows if r["view"] == view]
        by_view[view] = {
            name: sum(score_command(r, select(r))["correct"] for r in subset) / len(subset)
            for name, select in heuristics.items()
        }
        changed = [r for r in subset if r["phase"] == "after" and r["relevant_update"]]
        changed_by_view[view] = {
            name: sum(score_command(r, select(r))["correct"] for r in changed) / len(changed)
            for name, select in heuristics.items()
        }
        irrelevant = [r for r in subset if r["phase"] == "after" and not r["relevant_update"]]
        irrelevant_by_view[view] = {
            name: sum(score_command(r, select(r))["correct"] for r in irrelevant) / len(irrelevant)
            for name, select in heuristics.items()
        }
    return {
        "kind": "task_design_only",
        "version": VERSION,
        "split": "development",
        "n_scenarios": len({r["scenario_id"] for r in rows}),
        "n_variants": len(rows),
        "checksum": digest(rows),
        "answer_positions": dict(positions),
        "simulator_oracle_accuracy": sum(
            score_command(r, r["expected_command"])["correct"] for r in rows
        )
        / len(rows),
        "scripted_shortcut_accuracy_by_view": by_view,
        "scripted_shortcut_accuracy_after_relevant_update": changed_by_view,
        "scripted_shortcut_accuracy_after_irrelevant_update": irrelevant_by_view,
        "model_evidence": False,
        "confirmation_eligible": False,
        "note": "Variants share a scenario; these are simulator checks, not model results.",
    }


def export_design(output, seed=1729, scenarios=40):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Design output must be a new or empty directory")
    rows = build_design(seed, scenarios)
    summary = design_summary(rows)
    output.mkdir(parents=True, exist_ok=True)
    for name, records in (
        ("model_inputs.jsonl", [model_input(r) for r in rows]),
        ("oracle_rows.jsonl", rows),
    ):
        (output / name).write_text("".join(canonical(r) + "\n" for r in records))
    write_json(output / "summary.json", summary)
    # One deterministic illustration, never selected for a model's response.
    example = next(
        r
        for r in rows
        if r["updated"] == r["grant_variant"] == r["identity"] == r["rotation"] == 0
        and r["view"] == "self"
        and r["phase"] == "after"
    )
    write_json(output / "example.json", example)
    from .action_figure import render_design

    render_design(example, output / "action_design")
    write_json(
        output / "manifest.json",
        {
            "kind": "task_design_only",
            "version": VERSION,
            "seed": seed,
            "scenarios": scenarios,
            "design_checksum": summary["checksum"],
            "generator_sha256": file_hash(Path(__file__)),
            "source_hash": source_hash(),
            "model_evidence": False,
            "confirmation_eligible": False,
            "files": {p.name: file_hash(p) for p in sorted(output.iterdir()) if p.is_file()},
        },
    )
    return summary
