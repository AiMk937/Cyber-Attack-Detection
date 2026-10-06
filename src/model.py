"""Model definition plus helpers to save and load trained pipelines."""
from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.config import CATEGORICAL, SEED


def build_model(n_estimators: int = 300, class_weight: str | None = None) -> Pipeline:
    # One-hot encodes protocol/service/state and passes numeric features straight to the forest
    pre = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)],
        remainder="passthrough",
    )
    rf = RandomForestClassifier(
        n_estimators=n_estimators, class_weight=class_weight, n_jobs=-1, random_state=SEED
    )
    return Pipeline([("prep", pre), ("rf", rf)])


def save_model(model: Pipeline, features: list[str], path: Path) -> None:
    # Stores the pipeline together with its feature list so prediction can validate input
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features}, path, compress=3)


def load_model(path: Path) -> tuple[Pipeline, list[str]]:
    # Returns the trained pipeline and the feature columns it expects
    if not Path(path).exists():
        raise FileNotFoundError(f"No model at {path}. Train one first with: python -m src.train")
    bundle = joblib.load(path)
    return bundle["model"], bundle["features"]
