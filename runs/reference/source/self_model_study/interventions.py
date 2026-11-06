"""Intervention definitions and framework-independent array arithmetic."""

import numpy as np


def conditions(config):
    result = [{"id": "baseline", "kind": "none", "direction": "baseline", "strength": 0.0}]
    if config["phase"] == "baseline":
        return result
    if config["phase"] == "reference":
        return result + [
            {
                "id": f"historical:{direction}:{strength}",
                "kind": "absolute",
                "direction": direction,
                "strength": strength,
            }
            for direction, strength in [
                ("dense", 4.0),
                ("dense", 180.0),
                ("feature:11005", 120.0),
                ("feature:2728", 120.0),
                ("feature:10230", 120.0),
            ]
        ]
    spec = config["interventions"]
    directions = spec["directions"] + [f"random:{i}" for i in range(spec["random_count"])]
    if spec["combine"]:
        directions += ["combined:2728+10230"]
    for direction in directions:
        for strength in spec["strengths"]:
            result.append(
                {
                    "id": f"{direction}@{strength:+.3f}",
                    "kind": "relative",
                    "direction": direction,
                    "strength": strength,
                }
            )
    for fid in spec["ablate"]:
        result.append(
            {
                "id": f"ablate:{fid}",
                "kind": "ablate",
                "direction": f"feature:{fid}",
                "feature_id": fid,
                "strength": 0.0,
            }
        )
    return result


def unit(vector):
    vector = np.asarray(vector, dtype=np.float32)
    norm = np.linalg.norm(vector)
    if not np.isfinite(norm) or norm <= 1e-12:
        raise ValueError("Cannot normalize a zero/non-finite direction")
    return vector / norm


def residual_edit(
    residual, condition, directions, median_norm, encode=None, decoder=None, position="last"
):
    """NumPy reference implementation used as an independent oracle in hook tests."""
    if condition["kind"] == "none":
        return residual
    result = residual.copy()
    selection = result[:, -1:, :] if position == "last" else result
    if condition["kind"] == "ablate":
        fid = condition["feature_id"]
        # r = decode(f) + e; r' = r - f_i d_i preserves e and decoder bias.
        selection -= encode(selection)[..., fid : fid + 1] * decoder[fid]
    else:
        scale = median_norm if condition["kind"] == "relative" else 1.0
        selection += condition["strength"] * scale * directions[condition["direction"]]
    return result


def torch_hook(condition, directions, median_norm, sae, position="last"):
    """Last-position choice intervention; all-position generation is explicit."""

    def hook(residual, hook):
        if condition["kind"] == "none":
            return residual
        result = residual.clone()
        selection = result[:, -1:, :] if position == "last" else result
        if condition["kind"] == "ablate":
            fid = condition["feature_id"]
            encoded = sae.encode(selection.to(sae.W_enc.dtype))
            delta = encoded[..., fid : fid + 1] * sae.W_dec[fid]
            selection -= delta.to(selection.dtype)
        else:
            scale = median_norm if condition["kind"] == "relative" else 1.0
            vector = directions[condition["direction"]].to(
                device=selection.device, dtype=selection.dtype
            )
            selection += condition["strength"] * scale * vector
        return result

    return hook
