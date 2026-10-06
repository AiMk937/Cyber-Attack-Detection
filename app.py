"""Streamlit app: upload network flows and see which ones look like attacks.

Run with:  streamlit run app.py
"""
import json

import pandas as pd
import streamlit as st

from src.config import MODEL_DIR, REPORT_DIR, ROOT
from src.predict import AttackDetector

st.set_page_config(page_title="Cyber-Attack Detector", page_icon="🛡️", layout="wide")


@st.cache_resource
def get_detector() -> AttackDetector:
    # Loads the models once per session instead of on every interaction
    return AttackDetector(MODEL_DIR)


st.title("🛡️ Cyber-Attack Detector")
st.caption("Random Forest models trained on UNSW-NB15 network flows")

try:
    detector = get_detector()
except FileNotFoundError:
    st.error("No trained models found. Run `python -m src.train` first, then reload this page.")
    st.stop()

# Sidebar shows the model's test-set scores if training has been run
with st.sidebar:
    st.header("Model performance")
    metrics_file = REPORT_DIR / "metrics.json"
    if metrics_file.exists():
        m = json.loads(metrics_file.read_text())
        st.metric("Binary accuracy", f"{m['binary']['accuracy']:.1%}")
        st.metric("ROC-AUC", f"{m['binary']['roc_auc']:.3f}")
        st.metric("Category accuracy", f"{m['multiclass']['accuracy']:.1%}")
    threshold = st.slider("Attack threshold", 0.05, 0.95, 0.5, 0.05,
                          help="Flows with an attack probability at or above this are flagged")

source = st.radio("Data source", ["Use sample flows", "Upload a CSV"], horizontal=True)
if source == "Upload a CSV":
    upload = st.file_uploader("CSV with the UNSW-NB15 feature columns", type="csv")
    if upload is None:
        st.info("Upload a file to score it.")
        st.stop()
    flows = pd.read_csv(upload)
else:
    flows = pd.read_csv(ROOT / "examples" / "sample_flows.csv")

try:
    result = detector.predict(flows, threshold)
except ValueError as err:
    st.error(str(err))
    st.stop()

# Headline counts
attacks = result[result["predicted_label"] == "Attack"]
c1, c2, c3 = st.columns(3)
c1.metric("Flows scored", f"{len(result):,}")
c2.metric("Flagged as attack", f"{len(attacks):,}")
c3.metric("Attack rate", f"{len(attacks) / max(len(result), 1):.1%}")

# Compares against true labels when the file has them
if "label" in result.columns:
    truth = result["label"].map({0: "Normal", 1: "Attack"})
    st.success(f"Agreement with true labels: {(truth == result['predicted_label']).mean():.1%}")

left, right = st.columns(2)
with left:
    st.subheader("Predicted attack categories")
    if len(attacks):
        st.bar_chart(attacks["predicted_category"].value_counts())
    else:
        st.write("No attacks flagged.")
with right:
    st.subheader("Attack probability distribution")
    bands = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    binned = pd.cut(result["attack_probability"], bins=[0, .2, .4, .6, .8, 1.0], labels=bands, include_lowest=True)
    st.bar_chart(binned.value_counts().reindex(bands))

st.subheader("Results")
show = ["predicted_label", "predicted_category", "attack_probability", "proto", "service", "state", "sbytes", "dbytes"]
show += [c for c in ("attack_cat",) if c in result.columns]
st.dataframe(result[show].sort_values("attack_probability", ascending=False), width="stretch")

st.download_button("Download all predictions (CSV)", result.to_csv(index=False), "predictions.csv", "text/csv")
