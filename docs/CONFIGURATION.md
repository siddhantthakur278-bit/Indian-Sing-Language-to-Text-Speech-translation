# ML Pipeline Configuration Guide

This document describes all configuration parameters, integration contracts, directory paths, and runtime thresholds used across the Indian Sign Language (ISL) Machine Learning pipeline.

The single source of truth in code is [`ml/config.py`](file:///Users/parthnayak/Code/Projects_code/Group/Indian-Sing-Language-to-Text-Speech-translation/ml/config.py).

---

## 1. Directory Structure & Paths

| Variable | Default Value | Description |
|---|---|---|
| `BASE_DIR` | Repository root | Root directory of the project |
| `DATA_DIR` | `<root>/data` | Root folder for datasets and metadata |
| `CLASSES_PATH` | `<root>/data/classes.json` | Master vocabulary JSON mapping indices to glosses |
| `METADATA_PATH` | `<root>/data/metadata.csv` | Dataset clip registry and split assignments |
| `RAW_DATA_DIR` | `<root>/data/raw` | Raw video recordings organized by sign subdirectories |
| `PROCESSED_DATA_DIR` | `<root>/data/processed` | Extracted `.npy` landmark sequences per sign |
| `ARTIFACTS_DIR` | `<root>/ml/artifacts` | Saved models, evaluation plots, and sample vectors |
| `MODEL_CHECKPOINT` | `<root>/ml/artifacts/isl_model.keras` | Default model training checkpoint destination |
| `SAMPLE_IO_JSON` | `<root>/ml/sample_io.json` | Sample landmark test vectors for TypeScript parity |
| `SAMPLE_IO_NPZ` | `<root>/ml/artifacts/sample_io.npz` | NumPy archive of raw and normalized sample vectors |

---

## 2. Landmark Vector Layout (Contract 7.1)

Each frame extracted by MediaPipe Holistic produces a flat 258-dimensional float32 vector:

```
[0:132]   -> Pose landmarks: 33 points x (x, y, z, visibility)
[132:195] -> Left hand landmarks: 21 points x (x, y, z)
[195:258] -> Right hand landmarks: 21 points x (x, y, z)
```

| Parameter | Value | Description |
|---|---|---|
| `POSE_LANDMARKS` | `33` | Number of pose landmarks tracked by MediaPipe |
| `HAND_LANDMARKS` | `21` | Number of landmarks per hand (left and right) |
| `FEAT_DIM` | `258` | Total features per frame: `33*4 + 21*3 + 21*3 = 258` |
| `SEQ_LEN` / `SEQUENCE_LENGTH` | `30` | Resampled frame length per gesture sequence |
| `POSE_LEFT_SHOULDER_IDX` | `11` | Pose landmark index for the left shoulder |
| `POSE_RIGHT_SHOULDER_IDX` | `12` | Pose landmark index for the right shoulder |
| `EPSILON` | `1e-6` | Small constant added to shoulder distance to prevent zero division |

### Normalization Logic
1. Mid-shoulder midpoint: `center = (left_shoulder + right_shoulder) / 2.0`
2. Shoulder distance: `scale = ||left_shoulder - right_shoulder||_2 + 1e-6`
3. Translate coordinates relative to `center` and divide by `scale`
4. Pose visibility values (`[3, 7, 11, ...]`) are preserved untouched
5. Absent hands (all coordinates `< 1e-5`) remain strictly `0.0`

---

## 3. Signer-Wise Dataset Partitioning

To avoid identity leakage, clips must always be partitioned by signer ID rather than random splitting:

| Split | Default Signers | Description |
|---|---|---|
| Train | `["p01", "p02", "p03"]` | 60% of signers for model weight optimization |
| Validation | `["p04"]` | 20% of signers for early stopping and LR reduction |
| Test | `["p05"]` | 20% held-out unseen signers for final benchmarking |

---

## 4. Real-time Inference Thresholds

Thresholds governing browser Web Worker inference and the Python fallback demo:

| Parameter | Value | Description |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | `0.80` | Minimum softmax confidence required to accept a prediction |
| `VOTING_WINDOW` | `5` | Number of recent predictions evaluated for temporal consensus |
| `VOTING_CONSENSUS` | `4` | Required matching predictions out of `VOTING_WINDOW` |
| `COOLDOWN_FRAMES` | `30` | Refractory period (~1.0s at 30fps) before accepting the next sign |
| `PAUSE_THRESHOLD_MS` | `1500` | Inactivity duration without hands before sentence completion |
