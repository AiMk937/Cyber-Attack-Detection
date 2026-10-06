# :shield: Cyber-Attack Detection with Machine Learning

Random Forest models that detect malicious network traffic and classify the type of attack, trained on the **UNSW-NB15** intrusion detection dataset.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

---

## :dart: What it does

| Task | Question | Model |
| --- | --- | --- |
| **Binary detection** | Is this network flow normal or an attack? | Random Forest (300 trees) |
| **Attack categorization** | Which of 9 attack types (or normal) is it? | Random Forest (300 trees) |

---

## :bar_chart: Results

Evaluated on a stratified 20% hold-out set (16,467 flows).

### Binary detection

| Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | --- | --- | --- | --- |
| **97.6%** | 98.4% | 97.3% | 97.8% | **0.997** |

<p align="center"><img src="reports/figures/confusion_binary.png" width="380" /></p>

### Attack categorization (10 classes)

| Accuracy | Weighted F1 | Macro F1 |
| --- | --- | --- |
| **86.7%** | 0.861 | 0.510 |

| Category | F1 | | Category | F1 |
| --- | --- | --- | --- | --- |
| Generic | 0.98 | | Fuzzers | 0.68 |
| Normal | 0.97 | | Shellcode | 0.43 |
| Reconnaissance | 0.83 | | DoS | 0.37 |
| Exploits | 0.68 | | Analysis / Backdoor / Worms | < 0.15 |

<p align="center"><img src="reports/figures/confusion_multiclass.png" width="560" /></p>

Common, high-volume attacks are recognised well. Rare classes (Worms has only 44 samples in the whole dataset) are mostly confused with **Exploits**, since their flow statistics look similar.

### What drives the predictions

<p align="center"><img src="reports/figures/feature_importance.png" width="520" /></p>

Connection-count features (`ct_dst_src_ltm`, `ct_state_ttl`), bytes sent (`sbytes`) and time-to-live (`sttl`) are the strongest signals.

---

## :warning: Avoiding label leakage

An earlier version of this project reported **100% accuracy**. The cause was leakage, not a perfect model:

| Feature set | Accuracy |
| --- | --- |
| Includes `attack_cat` | 100.0% - `attack_cat == "Normal"` *is* the label |
| Includes `id` | 99.8% - row IDs are ordered by class |
| **Clean (both removed)** | **97.6%** |

Both columns are now excluded, and the notebook demonstrates the difference step by step.

---

## :file_folder: Project structure

```
Cyber-Attack-Detection/
├── data/
│   └── README.md                    # how to download UNSW-NB15
├── notebooks/
│   └── cyber_attack_detection.ipynb # walkthrough with results
├── reports/
│   ├── figures/                     # confusion matrices, feature importance
│   └── metrics.json                 # all scores from the last run
├── src/
│   └── train.py                     # trains both models and saves results
├── requirements.txt
└── LICENSE
```

---

## :rocket: Run it yourself

```bash
git clone https://github.com/AiMk937/Cyber-Attack-Detection.git
cd Cyber-Attack-Detection
pip install -r requirements.txt

# Download UNSW_NB15_training-set.csv into data/ (see data/README.md), then:
python src/train.py
```

Results are written to `reports/metrics.json` and `reports/figures/`. Training takes about 2-3 minutes on a laptop.

---

## :crystal_ball: Next steps

- Handle class imbalance with class weights or SMOTE to lift rare-attack recall
- Compare against gradient boosting (XGBoost / LightGBM)
- Test generalisation on the second official UNSW-NB15 partition instead of a random split

---

## :books: Dataset

Moustafa, N. and Slay, J. "UNSW-NB15: a comprehensive data set for network intrusion detection systems." *MilCIS*, IEEE, 2015.

## :page_with_curl: License

[MIT](LICENSE) - Aimaan Khan
