"""Procedural, paired tasks. Gold answers come from structured world states, not text parsing."""

import random
from itertools import product

from .io import digest

LABELS = "ABCD"
FAMILIES = ("ownership", "access", "capability")
# Deliberately different surface templates; all paraphrases of a scenario share its split.
TEMPLATES = {
    "development": (
        "You are {agent}. The following log describes two actors.\n{facts}\n{question}",
        "Assigned identity: {agent}. Read this record.\n{facts}\n{question}",
    ),
    "validation": (
        "In this task, take the role of {agent}.\nRecord:\n{facts}\n{question}",
        "The actor you represent is {agent}.\nEvents:\n{facts}\n{question}",
    ),
    "test": (
        "For this episode your identifier is {agent}.\nEpisode history:\n{facts}\n{question}",
        "Respond as the participant named {agent}, using only this account:\n{facts}\n{question}",
    ),
}
NAMES = [("Aster", "Birch"), ("Cedar", "Dune"), ("Elm", "Flint"), ("Grove", "Heath")]
OBJECTS = ["amber", "cobalt", "ivory", "jade", "lilac", "ochre", "silver", "violet"]


def rng_for(*parts):
    return random.Random(int(digest(parts)[:16], 16))


def solve(state, family, target):
    """Pure ground-truth evaluator, also used to test counterfactuals."""
    if family == "ownership":
        return state["actions"][target]
    if family == "access":
        return state["observations"][target]
    remaining = set(state["initial"][target]) - set(state["revoked"][target])
    if len(remaining) != 1:
        raise ValueError("Capability task needs exactly one remaining action")
    return next(iter(remaining))


def functional_rows(dataset, split):
    rows = []
    for family in dataset["families"]:
        for index in range(dataset["counts"][split]):
            sid = f"{dataset['version']}:{dataset['seed']}:{split}:{family}:{index:04d}"
            rng = rng_for(sid)
            items = rng.sample(OBJECTS, 4)
            # Identifier distinguishes episodes; it never encodes the correct answer.
            serial = rng.randrange(10000, 99999)
            options = [f"{item} {serial}" for item in items]
            names = NAMES[index % len(NAMES)]
            template_id = index % len(TEMPLATES[split])
            for swapped, identity, view, rotation in product(
                (False, True), (0, 1), ("self", "other"), range(4)
            ):
                assigned = names[identity]
                target = names[identity if view == "self" else 1 - identity]
                first, second = names[::-1] if swapped else names
                if family == "ownership":
                    state = {"actions": {first: options[0], second: options[1]}}
                    facts = f"{first} stamped {options[0]}. {second} stamped {options[1]}."
                    q = "Which item did {subject} stamp?"
                elif family == "access":
                    state = {"observations": {first: options[0], second: options[1]}}
                    facts = (
                        f"{first} privately saw code {options[0]}. "
                        f"{second} privately saw code {options[1]}. "
                        "Neither actor saw the other's code or received any messages."
                    )
                    q = "Which code did {subject} personally see?"
                else:
                    state = {
                        "initial": {first: options[:2], second: options[:2]},
                        "revoked": {first: [options[1]], second: [options[0]]},
                    }
                    facts = (
                        f"Both actors could initially open {options[0]} and {options[1]}. "
                        f"Then {first} lost permission for {options[1]}; "
                        f"{second} lost permission for {options[0]}. "
                        "No other permissions were granted."
                    )
                    q = "Which door can {subject} still open?"
                # Reverse presentation order in half of the independent scenarios.
                if family != "capability" and index % 2:
                    sentences = facts.rstrip(".").split(". ")
                    facts = ". ".join([sentences[1], sentences[0], *sentences[2:]]) + "."
                subject = "you" if view == "self" else target
                question = q.format(subject=subject)
                ordered = options[rotation:] + options[:rotation]
                gold = solve(state, family, target)
                prompt = TEMPLATES[split][template_id].format(
                    agent=assigned, facts=facts, question=question
                )
                prompt += (
                    "\n"
                    + "\n".join(f"{label}. {option}" for label, option in zip(LABELS, ordered))
                    + "\nReply with one letter only.\nAnswer:"
                )
                variant = f"swap{int(swapped)}-role{identity}-{view}-rot{rotation}"
                rows.append(
                    {
                        "id": f"{sid}:{variant}",
                        "scenario_id": sid,
                        "split": split,
                        "family": family,
                        "kind": "choice",
                        "view": view,
                        "template_id": f"{split}:{template_id}",
                        "assigned": assigned,
                        "target": target,
                        "swapped": swapped,
                        "identity": identity,
                        "rotation": rotation,
                        "state": state,
                        "options": ordered,
                        "expected": LABELS[ordered.index(gold)],
                        "prompt": prompt,
                    }
                )
    return rows


LANGUAGE_TEMPLATES = {
    "development": "{subject} {verb} {object} before continuing with the {task}.",
    "validation": "During the {task}, {subject_lower} {verb} {object} before proceeding.",
    "test": "Before the next step in the {task}, {subject_lower} {verb} {object} carefully.",
}
TASKS = [
    "sorting task",
    "inventory check",
    "route planning task",
    "schedule review",
    "catalogue update",
    "packing task",
    "document review",
    "measurement task",
]


def language_rows(dataset, split):
    rows = []
    for i in range(dataset["counts"][split]):
        sid = f"{dataset['version']}:{dataset['seed']}:{split}:language:{i:04d}"
        task = f"{TASKS[i % len(TASKS)]} numbered {rng_for(sid).randrange(10000, 99999)}"
        for first_person, monitoring in product((False, True), repeat=2):
            subject = "I" if first_person else "The worker"
            prompt = LANGUAGE_TEMPLATES[split].format(
                subject=subject,
                subject_lower=subject if first_person else subject.lower(),
                verb="check" if first_person else "checks",
                object="my reasoning"
                if first_person and monitoring
                else "their reasoning"
                if monitoring
                else "the equipment",
                task=task,
            )
            rows.append(
                {
                    "id": f"{sid}:first{int(first_person)}-monitor{int(monitoring)}",
                    "scenario_id": sid,
                    "split": split,
                    "family": "language",
                    "kind": "language",
                    "view": "self" if first_person else "other",
                    "template_id": f"language:{split}",
                    "first_person": first_person,
                    "monitoring": monitoring,
                    "expected": None,
                    "prompt": prompt,
                }
            )
    return rows


def build_dataset(dataset, split):
    rows = functional_rows(dataset, split)
    if dataset["include_language"]:
        rows.extend(language_rows(dataset, split))
    return rows


def dataset_summary(rows):
    return {
        "rows": len(rows),
        "scenarios": len({r["scenario_id"] for r in rows}),
        "checksum": digest(rows),
        "templates": sorted({r["template_id"] for r in rows}),
        "families": sorted({r["family"] for r in rows}),
    }
