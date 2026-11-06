from collections import Counter, defaultdict

from self_model_study.data import LABELS, build_dataset, functional_rows, solve


def test_deterministic_and_disjoint_splits(config):
    pools, templates = [], []
    for split in ("development", "validation", "test"):
        rows = build_dataset(config["dataset"], split)
        assert rows == build_dataset(config["dataset"], split)
        assert len({r["id"] for r in rows}) == len(rows)
        pools.append({r["scenario_id"] for r in rows})
        templates.append({r["template_id"] for r in rows})
    for i in range(3):
        for j in range(i):
            assert pools[i].isdisjoint(pools[j])
            assert templates[i].isdisjoint(templates[j])


def test_gold_balancing_and_counterfactuals(config):
    rows = functional_rows(config["dataset"], "development")
    groups = defaultdict(list)
    lookup = {}
    for row in rows:
        assert ".." not in row["prompt"]
        assert row["options"][LABELS.index(row["expected"])] == solve(
            row["state"], row["family"], row["target"]
        )
        groups[row["scenario_id"]].append(row)
        key = (row["scenario_id"], row["identity"], row["view"], row["rotation"], row["swapped"])
        lookup[key] = row
    for group in groups.values():
        assert len(group) == 32
        assert Counter(r["expected"] for r in group) == dict.fromkeys(LABELS, 8)
    for key, row in lookup.items():
        swapped = lookup[(*key[:-1], not key[-1])]
        assert row["expected"] != swapped["expected"]
        alternate = lookup[(key[0], 1 - key[1], key[2], key[3], key[4])]
        assert row["expected"] != alternate["expected"]


def test_planned_counts(config):
    config["dataset"]["counts"] = {"development": 40, "validation": 40, "test": 100}
    for split, count in config["dataset"]["counts"].items():
        rows = build_dataset(config["dataset"], split)
        for family in config["dataset"]["families"]:
            assert len({r["scenario_id"] for r in rows if r["family"] == family}) == count
        assert len([r for r in rows if r["kind"] == "language"]) == count * 4


def test_language_factorial(config):
    rows = [r for r in build_dataset(config["dataset"], "development") if r["kind"] == "language"]
    groups = defaultdict(set)
    for row in rows:
        groups[row["scenario_id"]].add((row["first_person"], row["monitoring"]))
    assert all(
        v == {(False, False), (False, True), (True, False), (True, True)} for v in groups.values()
    )
