"""Predict whether network flows are attacks, and which type, using the saved models.

Usage:
    python -m src.predict path/to/flows.csv
    python -m src.predict path/to/flows.csv --output results.csv --threshold 0.7
"""
import argparse
from pathlib import Path

import pandas as pd

from src.config import BINARY_MODEL, MODEL_DIR, MULTICLASS_MODEL
from src.data import prepare_features
from src.model import load_model


class AttackDetector:
    """Loads both saved models once and scores any DataFrame of flows."""

    def __init__(self, model_dir: Path = MODEL_DIR):
        self.binary, self.features = load_model(model_dir / BINARY_MODEL)
        self.multi, _ = load_model(model_dir / MULTICLASS_MODEL)

    def predict(self, flows: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        # Adds attack probability, a Normal/Attack verdict and the most likely attack category
        X = prepare_features(flows, self.features)
        result = flows.copy()
        proba = self.binary.predict_proba(X)[:, 1]
        result["attack_probability"] = proba.round(4)
        result["predicted_label"] = ["Attack" if p >= threshold else "Normal" for p in proba]
        category = self.multi.predict(X)
        # Keeps the category consistent with the binary verdict
        result["predicted_category"] = [
            "Normal" if lbl == "Normal" else (cat if cat != "Normal" else "Unknown attack")
            for lbl, cat in zip(result["predicted_label"], category)
        ]
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Score network flows with the trained models.")
    parser.add_argument("input", type=Path, help="CSV of flows with the UNSW-NB15 feature columns")
    parser.add_argument("--models", type=Path, default=MODEL_DIR)
    parser.add_argument("--output", type=Path, default=Path("predictions.csv"))
    parser.add_argument("--threshold", type=float, default=0.5, help="Attack probability cut-off (0-1)")
    args = parser.parse_args()

    result = AttackDetector(args.models).predict(pd.read_csv(args.input), args.threshold)
    result.to_csv(args.output, index=False)

    print(f"Scored {len(result):,} flows\n")
    print(result["predicted_label"].value_counts().to_string())
    attacks = result[result["predicted_label"] == "Attack"]
    if len(attacks):
        print("\nAttack categories:")
        print(attacks["predicted_category"].value_counts().to_string())
    print(f"\nPredictions saved to {args.output}")


if __name__ == "__main__":
    main()
