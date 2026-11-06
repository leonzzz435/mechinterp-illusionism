from copy import deepcopy

import pytest

from self_model_study.config import DEFAULTS, validate_config


@pytest.fixture
def config():
    c = deepcopy(DEFAULTS)
    c.update(backend="mock", phase="exploratory", split="development")
    c["dataset"]["counts"] = {"development": 2, "validation": 2, "test": 3}
    c["interventions"].update(directions=["feature:2728"], strengths=[0.05], random_count=0)
    c["generation"]["seeds"] = [42]
    c["statistics"]["bootstrap_samples"] = 1000
    return validate_config(c)
