"""Train, evaluate and save Random Forest models for cyber-attack detection on UNSW-NB15.

Usage:
    python -m src.train
    python -m src.train --trees 500 --class-weight balanced
"""
import argparse
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split

from src.config import (BINARY_MODEL, DATA_PATH, LABEL_NAMES, MODEL_DIR, MULTICLASS_MODEL,
                        REPORT_DIR, SEED, TEST_SIZE)
from src.data import feature_columns, load_dataset
from src.model import build_model, save_model


def save_confusion(y_true, y_pred, labels, title, path, normalize=None) -> None:
    # Saves a confusion matrix image for the README
    fig, ax = plt.subplots(figsize=(7, 6) if len(labels) > 2 else (5, 4))
    ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred, labels=labels, display_labels=labels, normalize=normalize,
        values_format=".2f" if normalize else "d", cmap="Blues", ax=ax, colorbar=False,
    )
    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_importance(model, path: Path, top: int = 15) -> None:
    # Plots the features the Random Forest relied on most
    names = [n.split("__", 1)[1] for n in model.named_steps["prep"].get_feature_names_out()]
    imp = pd.Series(model.named_steps["rf"].feature_importances_, index=names).nlargest(top)[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    imp.plot.barh(ax=ax, color="#2563eb")
    ax.set_title(f"Top {top} features - binary model")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run(data_path: Path, report_dir: Path, model_dir: Path, n_estimators: int, class_weight: str | None) -> dict:
    start = time.time()
    fig_dir = report_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset(data_path)
    features = feature_columns(df)
    X = df[features]
    print(f"Loaded {len(df):,} flows with {len(features)} features")

    # Same stratified split for both tasks so their results are comparable
    idx_train, idx_test = train_test_split(df.index, test_size=TEST_SIZE, stratify=df["attack_cat"], random_state=SEED)
    X_train, X_test = X.loc[idx_train], X.loc[idx_test]

    # Task 1: binary detection (normal vs attack)
    print("Training binary model...")
    y_train, y_test = df.loc[idx_train, "label"], df.loc[idx_test, "label"]
    binary = build_model(n_estimators, class_weight).fit(X_train, y_train)
    pred = binary.predict(X_test)
    proba = binary.predict_proba(X_test)[:, 1]
    binary_metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
    }
    names = list(LABEL_NAMES.values())
    save_confusion(y_test.map(LABEL_NAMES).values, pd.Series(pred).map(LABEL_NAMES).values, names,
                   "Binary detection - confusion matrix", fig_dir / "confusion_binary.png")
    save_importance(binary, fig_dir / "feature_importance.png")

    # Task 2: multi-class attack categorization
    print("Training multi-class model...")
    yc_train, yc_test = df.loc[idx_train, "attack_cat"], df.loc[idx_test, "attack_cat"]
    multi = build_model(n_estimators, class_weight).fit(X_train, yc_train)
    cpred = multi.predict(X_test)
    report = classification_report(yc_test, cpred, output_dict=True, zero_division=0)
    multi_metrics = {
        "accuracy": accuracy_score(yc_test, cpred),
        "macro_f1": f1_score(yc_test, cpred, average="macro"),
        "weighted_f1": f1_score(yc_test, cpred, average="weighted"),
        "per_class_f1": {k: v["f1-score"] for k, v in report.items()
                         if isinstance(v, dict) and k not in ("macro avg", "weighted avg")},
    }
    save_confusion(yc_test.values, cpred, yc_test.value_counts().index.tolist(),
                   "Attack categories - normalized confusion matrix",
                   fig_dir / "confusion_multiclass.png", normalize="true")

    # Saves both trained pipelines so predict.py and the app can reuse them without retraining
    save_model(binary, features, model_dir / BINARY_MODEL)
    save_model(multi, features, model_dir / MULTICLASS_MODEL)

    metrics = {
        "rows": len(df), "test_rows": len(idx_test), "trees": n_estimators,
        "class_weight": class_weight, "binary": binary_metrics, "multiclass": multi_metrics,
    }
    (report_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(f"\nBinary      accuracy {binary_metrics['accuracy']:.4f} | F1 {binary_metrics['f1']:.4f} | ROC-AUC {binary_metrics['roc_auc']:.4f}")
    print(f"Multi-class accuracy {multi_metrics['accuracy']:.4f} | macro F1 {multi_metrics['macro_f1']:.4f}")
    print(f"Models saved to {model_dir}/, reports to {report_dir}/ ({time.time() - start:.0f}s)")
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train cyber-attack detection models on UNSW-NB15.")
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="Path to the labelled CSV")
    parser.add_argument("--reports", type=Path, default=REPORT_DIR, help="Where to write metrics and figures")
    parser.add_argument("--models", type=Path, default=MODEL_DIR, help="Where to save trained models")
    parser.add_argument("--trees", type=int, default=300, help="Number of trees per forest")
    parser.add_argument("--class-weight", choices=["balanced"], default=None,
                        help="Use 'balanced' to up-weight rare attack categories")
    return parser.parse_args()


if __name__ == "__main__":
    a = parse_args()
    run(a.data, a.reports, a.models, a.trees, a.class_weight)
