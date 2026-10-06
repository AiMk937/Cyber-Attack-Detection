"""Smoke tests that train tiny models on the bundled sample and check predictions end to end."""
from pathlib import Path

import pandas as pd
import pytest

from src.config import ROOT
from src.data import clean, feature_columns, prepare_features
from src.predict import AttackDetector
from src.train import run

SAMPLE = ROOT / "examples" / "sample_flows.csv"


@pytest.fixture(scope="module")
def trained(tmp_path_factory) -> Path:
    # Trains small forests once and shares the output folder across tests
    out = tmp_path_factory.mktemp("run")
    run(SAMPLE, out / "reports", out / "models", n_estimators=10, class_weight=None)
    return out


def test_leaky_columns_are_never_features():
    cols = feature_columns(clean(pd.read_csv(SAMPLE)))
    assert not {"id", "attack_cat", "label"} & set(cols)


def test_training_writes_models_and_reports(trained):
    assert (trained / "models" / "binary_model.joblib").exists()
    assert (trained / "models" / "multiclass_model.joblib").exists()
    assert (trained / "reports" / "metrics.json").exists()
    assert (trained / "reports" / "figures" / "confusion_binary.png").exists()


def test_predictions_have_expected_columns(trained):
    flows = pd.read_csv(SAMPLE).drop(columns=["label", "attack_cat"])
    result = AttackDetector(trained / "models").predict(flows)
    assert len(result) == len(flows)
    assert set(result["predicted_label"]) <= {"Normal", "Attack"}
    assert result["attack_probability"].between(0, 1).all()


def test_missing_columns_raise_clear_error(trained):
    detector = AttackDetector(trained / "models")
    with pytest.raises(ValueError, match="missing"):
        prepare_features(pd.DataFrame({"proto": ["tcp"]}), detector.features)
