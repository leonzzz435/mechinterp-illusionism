import numpy as np
import pytest

from self_model_study.interventions import residual_edit, torch_hook, unit


def test_unit_zero_fails():
    with pytest.raises(ValueError):
        unit(np.zeros(3))


def test_zero_and_last_position():
    x = np.ones((2, 3, 4))
    vectors = {"v": np.array([1.0, 0, 0, 0])}
    assert residual_edit(x, {"kind": "none"}, vectors, 10) is x
    condition = {"kind": "relative", "direction": "v", "strength": 0.1}
    result = residual_edit(x, condition, vectors, 10)
    np.testing.assert_equal(result[:, :-1], x[:, :-1])
    np.testing.assert_equal(result[:, -1, 0], [2, 2])
    np.testing.assert_equal(x, np.ones_like(x))


def test_ablation_preserves_reconstruction_error_and_bias():
    decoder = np.array([[1.0, 0, 0], [0.5, 1, 0]])
    features = np.array([[[2.0, 3.0]]])
    bias = np.array([0.3, 0.2, 0.1])
    error = np.array([[[0.1, -0.1, 5.0]]])
    residual = features @ decoder + bias + error
    condition = {"kind": "ablate", "feature_id": 0}
    result = residual_edit(residual, condition, {}, 0, lambda x: features, decoder)
    reduced = features.copy()
    reduced[..., 0] = 0
    np.testing.assert_allclose(result - (reduced @ decoder + bias), error)
    # Nonorthogonal directions: the intervention makes no claim of re-encoded independence.
    assert decoder[0] @ decoder[1] != 0


@pytest.mark.parametrize("position", ["last", "all"])
@pytest.mark.parametrize("kind", ["none", "relative", "absolute", "ablate"])
def test_torch_matches_numpy_oracle(position, kind):
    torch = pytest.importorskip("torch")
    x = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
    decoder = np.eye(4, dtype=np.float32)
    vectors = {"v": unit(np.array([1, 2, 3, 4]))}
    condition = {"kind": kind, "direction": "v", "strength": -0.05, "feature_id": 1}

    class SAE:
        W_enc = torch.eye(4)
        W_dec = torch.eye(4)

        def encode(self, value):
            return value.relu()

    expected = residual_edit(
        x, condition, vectors, 3.0, lambda t: np.maximum(t, 0), decoder, position
    )
    hook = torch_hook(
        condition, {k: torch.tensor(v) for k, v in vectors.items()}, 3.0, SAE(), position
    )
    actual = hook(torch.tensor(x), None).numpy()
    np.testing.assert_allclose(actual, expected, atol=1e-6)
