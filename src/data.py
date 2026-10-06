"""Loading, cleaning and validating UNSW-NB15 flow data."""
from pathlib import Path

import pandas as pd

from src.config import CATEGORICAL, NON_FEATURES


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Normalises text columns so training and prediction see identical values
    df = df.copy()
    for col in CATEGORICAL:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
    if "service" in df.columns:
        df["service"] = df["service"].replace("-", "none")
    return df


def load_dataset(path: Path) -> pd.DataFrame:
    # Reads the labelled dataset and checks the target columns are present
    if not Path(path).exists():
        raise FileNotFoundError(f"Dataset not found at {path}. See data/README.md for download steps.")
    df = clean(pd.read_csv(path))
    missing = {"label", "attack_cat"} - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing target columns: {sorted(missing)}")
    df["attack_cat"] = df["attack_cat"].astype(str).str.strip()
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
    # Every column except the id and the two targets
    return [c for c in df.columns if c not in NON_FEATURES]


def prepare_features(df: pd.DataFrame, expected: list[str]) -> pd.DataFrame:
    # Cleans new data and lines its columns up with what the model was trained on
    df = clean(df)
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Input is missing {len(missing)} feature column(s): {missing[:8]}")
    return df[expected]
