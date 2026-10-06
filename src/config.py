"""Shared paths and constants used across training, prediction and the app."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "UNSW_NB15_training-set.csv"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

BINARY_MODEL = "binary_model.joblib"
MULTICLASS_MODEL = "multiclass_model.joblib"

CATEGORICAL = ["proto", "service", "state"]
# id and attack_cat are excluded on purpose: both leak the label and inflate accuracy to ~100%
NON_FEATURES = ["id", "attack_cat", "label"]
LABEL_NAMES = {0: "Normal", 1: "Attack"}

SEED = 42
TEST_SIZE = 0.2
