"""A simulator-derived explanatory figure, never a model-result plot."""


def render_design(row, stem):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    from .reporting import save_figure

    actor = row["assigned"]
    other = next(a for a in row["before"]["permissions"] if a != actor)
    event = row["event"]
    fig, ax = plt.subplots(figsize=(12, 5.8))
    fig.patch.set_facecolor("#f7f7f2")
    ax.set(xlim=(0, 12), ylim=(0, 5.8))
    ax.axis("off")
    ax.text(
        6,
        5.4,
        "Does the action follow the changed permission?",
        ha="center",
        fontsize=18,
        weight="bold",
    )
    boxes = [
        (
            0.3,
            "1  Initial state",
            f"Active connection: {actor}\n\n"
            f"{actor}: {row['before']['permissions'][actor][0]}\n"
            f"{other}: {row['before']['permissions'][other][0]}",
        ),
        (
            4.35,
            "2  Simulator update",
            f"For {event['actor']}:\n\nRevoke {event['revoke']}\nGrant {event['grant']}",
        ),
        (
            8.4,
            "3  Check the action",
            f"For {actor}:\n\n{event['revoke']} → rejected\n{event['grant']} → marker added",
        ),
    ]
    for x, title, body in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, 2.6),
                3.25,
                2.1,
                boxstyle="round,pad=0.1",
                facecolor="white",
                edgecolor="#005f73",
                linewidth=1.6,
            )
        )
        ax.text(x + 0.12, 4.3, title, fontsize=12, weight="bold")
        ax.text(x + 0.12, 3.45, body, fontsize=10, va="center", linespacing=1.5)
    for x in (3.7, 7.75):
        ax.add_patch(
            FancyArrowPatch(
                (x, 3.6),
                (x + 0.45, 3.6),
                arrowstyle="-|>",
                mutation_scale=16,
                color="#005f73",
            )
        )
    ax.text(
        6, 1.85, "Three matched views of the same episode", ha="center", fontsize=13, weight="bold"
    )
    ax.text(
        6,
        1.25,
        f"Your connection ({actor})     ·     {actor} named explicitly     ·     Other ({other})",
        ha="center",
        fontsize=11,
    )
    ax.text(
        6,
        0.8,
        "The other connection keeps its permission. Command order rotates.",
        ha="center",
        fontsize=10,
        color="#475569",
    )
    ax.text(
        6,
        0.25,
        "TASK DESIGN ONLY · Outcomes above are simulator rules, not LLM results",
        ha="center",
        fontsize=10,
        weight="bold",
        color="#475569",
    )
    plt.rcParams["svg.fonttype"] = "none"
    save_figure(fig, stem)
    plt.close(fig)
    # Matplotlib's SVG path serializer adds trailing spaces; keep committed figures clean.
    svg = stem.with_suffix(".svg")
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
