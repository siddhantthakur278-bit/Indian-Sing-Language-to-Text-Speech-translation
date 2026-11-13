# AGENTS.md for PARTH: Data + ML Track (ISL Translator)

> Give this file to the AI agent that works on **Parth's part only**. Save it in the repo root as `AGENTS.md` (or paste it as the first prompt). Read it fully before writing code.

---

## 0. How you (the agent) should work

1. Read this whole file, then reply with a short plan and **wait for confirmation** before generating code.
2. Work **task by task** (Section 10). One task ID per commit: `[P5] baseline BiLSTM`.
3. **Stay inside your folders:** `data/`, `ml/`, `notebooks/`. Do **not** edit `web/` or `backend/` (owned by Siddhant and Abhi). If a change there is needed, write it as a request in `docs/requests.md`.
4. **Never invent data or results.** Do not fabricate datasets, labels, accuracy numbers, confusion matrices or plots. If data is missing, say so, build the pipeline against a tiny synthetic stub clearly marked `MOCK`, and tell Parth what to supply.
5. **Report real numbers only,** from real runs, with the split used.
6. After each task report: what changed, how to run it, how you tested it, what is still open.
7. When unsure about library APIs (MediaPipe, TensorFlow, TF.js converter), **check the official docs** and note which version you used.
8. Ask before adding heavy dependencies or changing the contracts in Section 5.

---

## 1. Project context (short)

**Goal:** real-time translation of **Indian Sign Language (ISL)** to text and speech in Indian languages (Ministry of Social Justice and Empowerment; ISLRTC / DePWD, 2024, Software).

```
Camera -> MediaPipe landmarks -> normalize + 30-frame buffer -> SIGN MODEL (you) -> glosses
-> sentence (Abhi) -> translation + speech (Abhi) -> web app (Siddhant)
```

**Your job:** produce a **sign recognition model** that takes a 30-frame landmark sequence and outputs one gloss (or `IDLE`), small and fast enough to run **in the browser**.

Team: Siddhant (frontend + integration), **Parth (you: data + ML)**, Abhi (NLP, speech, backend).

---

## 2. Your deliverables (handoff to the team)

| Deliverable | Path | Consumer |
|---|---|---|
| Gloss list (single source of truth) | `data/classes.json` | everyone |
| Keypoint extraction + preprocessing scripts | `ml/*.py` | team |
| Trained model | `ml/artifacts/isl_model.keras` | Parth |
| Browser model (quantized) | `ml/artifacts/web_model/` | Siddhant |
| Test vectors for the TS port | `ml/artifacts/sample_io.npz` (+ `sample_io.json`) | Siddhant |
| Evaluation report | `docs/ml_evaluation.md` + images | everyone |
| Model card | `docs/model_card.md` | everyone |
| OpenCV real-time fallback demo | `ml/realtime_demo.py` | demo day |

---

## 3. Folder structure (yours)

```
data/
|-- raw/                     # NOT committed: raw/<GLOSS>/<GLOSS>_p<signer>_<nnn>.mp4
|-- processed/               # NOT committed: processed/<GLOSS>/<clip>.npy  shape (30, 258)
|-- metadata.csv             # committed: clip, gloss, signer_id, split, source, quality_flag
|-- classes.json             # committed
`-- README_data.md           # how data was collected, licences, consent notes
ml/
|-- config.py                # SEQ_LEN=30, FEATURES=258, THRESHOLD=0.8 ...
|-- extract_keypoints.py
|-- preprocess.py            # normalize(), augment(), make_splits()
|-- dataset.py               # loads .npy + metadata into arrays/tf.data
|-- train.py
|-- evaluate.py
|-- export_tfjs.sh
|-- realtime_demo.py
|-- requirements.txt
`-- artifacts/               # models, plots, sample_io (large files not committed)
notebooks/                   # Colab versions of training
docs/
```

---

## 4. Environment

- Python 3.10 or 3.11. Create a venv. Use versions that are at least a couple of weeks old and pin them in `ml/requirements.txt`.
- Packages: `mediapipe, opencv-python, numpy, pandas, scikit-learn, matplotlib, tensorflow (or torch), tensorflowjs`.
- GPU optional; provide a Colab/Kaggle notebook for training.

---

## 5. Contracts (do not change without asking)

### 5.1 Landmark vector (must match the browser exactly)

258 values per frame:

| Slice | Content | Size |
|---|---|---|
| 0:132 | Pose: 33 landmarks x (x, y, z, visibility) | 132 |
| 132:195 | Left hand: 21 x (x, y, z) | 63 |
| 195:258 | Right hand: 21 x (x, y, z) | 63 |

- Missing pose or hand: zeros.
- Normalization: subtract the mid-shoulder point (pose landmarks 11 and 12) and divide by shoulder width (+1e-6) for pose x, y, z and both hands. Visibility unchanged.
- Sequence length 30 via `np.linspace(0, n-1, 30).astype(int)` resampling.
- Model input `(batch, 30, 258)`; output softmax over `classes.json` (index = array position; `IDLE` included).

Reference implementation to start from (verify it, then add unit tests):

```python
import numpy as np

def normalize(seq: np.ndarray) -> np.ndarray:          # seq: (T, 258)
    out = seq.astype(np.float32).copy()
    pose = out[:, :132].reshape(-1, 33, 4)
    ls, rs = pose[:, 11, :3], pose[:, 12, :3]
    center = (ls + rs) / 2
    scale = np.linalg.norm(ls - rs, axis=1, keepdims=True) + 1e-6
    pose[:, :, :3] = (pose[:, :, :3] - center[:, None]) / scale[:, None]
    lh = (out[:, 132:195].reshape(-1, 21, 3) - center[:, None]) / scale[:, None]
    rh = (out[:, 195:258].reshape(-1, 21, 3) - center[:, None]) / scale[:, None]
    T = len(seq)
    return np.concatenate([pose.reshape(T, -1), lh.reshape(T, -1), rh.reshape(T, -1)], axis=1)
```

Decision to record in `docs/model_card.md`: absent hands are zeros **before** normalization; check whether normalizing zeros creates artifacts, and if so mask absent hands after normalization (then tell Siddhant so `normalize.ts` matches).

### 5.2 Gloss naming

UPPERCASE English with underscores: `HELLO, THANK_YOU, HOSPITAL`. Include `IDLE`. Never reorder `classes.json` after training; bump `version` instead.

```json
{ "version": 1, "classes": ["IDLE", "HELLO", "THANK_YOU"] }
```

### 5.3 Runtime thresholds (used by the frontend; you choose values from evaluation)

Default: confidence >= 0.8, 4 of last 5 predictions agree, 1 s cooldown. Report if evaluation suggests different values.

---

## 6. Vocabulary (MVP, about 60 classes)

Starter list; finalise against the ISLRTC dictionary and agree with the team in week 1:

- Greetings: `HELLO, THANK_YOU, SORRY, PLEASE, WELCOME, GOODBYE`
- People: `ME, YOU, HE_SHE, MOTHER, FATHER, FRIEND, DOCTOR, TEACHER`
- Emergency: `HELP, PAIN, POLICE, HOSPITAL, FIRE, MEDICINE, WATER`
- Daily: `FOOD, EAT, DRINK, TOILET, MONEY, HOME, SCHOOL, MARKET`
- Verbs: `GO, COME, WANT, NEED, KNOW, UNDERSTAND, STOP, WAIT`
- Questions: `WHAT, WHERE, WHEN, WHO, WHY, HOW`
- Numbers: `ONE ... TEN`
- Special: `IDLE`

`IDLE` samples: hands down, adjusting clothes or hair, resting, random non-sign movement, transitions. Aim for as many samples as the largest sign class.

---

## 7. Module specifications

### 7.1 Data collection and organisation (P1, P2)

- Sources: INCLUDE dataset (AI4Bharat) subset matching the vocabulary; ISLRTC dictionary videos as reference; **own recordings**.
- Own recordings: 30-50 clips per sign, 2-3 s, 30 fps, several signers (3-5 or more), varied light, background and distance, left- and right-handed signers.
- Naming: `data/raw/HELLO/HELLO_p01_003.mp4`.
- `metadata.csv` columns: `clip, gloss, signer_id, split, source, quality_flag`.
- Consent from every signer; keep raw data out of Git; check dataset licences and record them in `README_data.md`.

### 7.2 Keypoint extraction (P3)

- MediaPipe Holistic, `min_detection_confidence=0.5`, `min_tracking_confidence=0.5`, RGB frames.
- Output `(30, 258)` `.npy` per clip; batch script with progress bar and resume.
- Flag clips where hands are missing in more than 50% of frames (`quality_flag`); do not silently drop.

### 7.3 Preprocessing and splits (P4)

- `normalize()` per 5.1, with unit tests (shape, shoulder-center becomes 0, scale invariance, missing-hand handling).
- Augmentations (training only): scale 0.9-1.1, rotation within +/-10 degrees, translation jitter, time warp 0.8-1.2x, frame dropout 5-10%, Gaussian noise; mirroring only with correct left/right swap and only if justified.
- **Signer-wise split** (for example signers 1-6 train, 7 validation, 8 test). Never split randomly by clip. Save split assignments in `metadata.csv`.

### 7.4 Baseline model (P5)

```python
model = models.Sequential([
    layers.Input(shape=(30, 258)),
    layers.Masking(mask_value=0.0),
    layers.Bidirectional(layers.LSTM(128, return_sequences=True)),
    layers.Dropout(0.3),
    layers.Bidirectional(layers.LSTM(64)),
    layers.Dropout(0.3),
    layers.Dense(128, activation="relu"),
    layers.Dense(NUM_CLASSES, activation="softmax"),
])
```

- Adam (1e-3), sparse categorical cross-entropy, early stopping (patience about 12), ReduceLROnPlateau, class weights if imbalanced, fixed random seeds, log each run to `ml/artifacts/runs/<timestamp>/` (config, metrics, curves).
- Check the mask: `Masking` with zero-filled frames can hide real data; verify it behaves as intended.

### 7.5 Improvements (P6)

Try, one at a time, and keep a results table: velocity features (frame differences), 1D-CNN + BiLSTM, small Transformer encoder, hand-relative features, stronger augmentation, label smoothing, more signers. Review the confusion matrix and fix the most confused pairs with data first, then features, then architecture. Keep the final model small (target under about 10-20 MB after quantization).

### 7.6 Export for the browser (P7)

- Convert with the TF.js converter; quantize (float16 or int8) and compare accuracy before/after.
- Write `sample_io.npz` and `sample_io.json` with at least 10 raw sequences, their normalized arrays and the model's output probabilities, so Siddhant can test `normalize.ts` (tolerance 1e-4) and the in-browser model.
- Document input/output tensor names and shapes in `docs/model_card.md`.
- ONNX export is an optional alternative.

### 7.7 Real-time Python demo (P8)

`ml/realtime_demo.py`: OpenCV webcam loop with a 30-frame deque, prediction every 3 frames, threshold 0.8, voting, cooldown, skeleton overlay, on-screen glosses. It is the fallback demo if the browser version fails.

### 7.8 Evaluation (P9)

Report on the **held-out signers** only:
- top-1 and top-5 accuracy, per-class precision/recall/F1, confusion matrix image;
- performance with and without `IDLE`, and false-trigger rate on idle video;
- robustness: bright, dim, backlit, cluttered background, different distances;
- inference latency (ms) in Python and in the browser (coordinate with Siddhant);
- list of the 10 worst classes with likely causes and fixes.

Write results to `docs/ml_evaluation.md`; every number must come from a real run, with the command used.

---

## 8. Acceptance criteria

- [ ] `data/classes.json` approved by the team; model output order matches it.
- [ ] Extraction pipeline reproducible with one command; quality log produced.
- [ ] Signer-wise split documented in `metadata.csv`.
- [ ] Baseline reaches at least 85% validation accuracy on held-out signers (report the real number honestly, even if lower, with analysis).
- [ ] `IDLE` class present and evaluated.
- [ ] `normalize()` unit tests pass; `sample_io` files delivered.
- [ ] Quantized TF.js model loads in a browser and matches Python outputs closely on the sample inputs.
- [ ] Evaluation report and model card written.

---

## 9. Safety, privacy and ethics

- Raw videos and landmarks are personal data of signers: keep them out of Git, get consent, anonymise file names, and never upload them to third-party services without permission.
- Do not claim accuracy beyond what was measured; state vocabulary size, number of signers and limitations (regional variation, lighting, skin tones, clothing) in the model card.
- Credit ISLRTC and AI4Bharat (INCLUDE) and follow dataset licences.
- No secrets in the repo.

---

## 10. Task list

| ID | Task | Week | Done when |
|---|---|---|---|
| P1 | Study ISL basics; finalise vocabulary; create `classes.json` | W1 | Shared and approved |
| P2 | Data collection plan, INCLUDE subset, own recordings, `metadata.csv`, `IDLE` data | W1-2 | Counts per class table |
| P3 | `extract_keypoints.py` + batch run + quality flags | W1-2 | `.npy` files `(30,258)` created |
| P4 | `preprocess.py`: normalize, augment, signer-wise splits, tests | W2 | Tests pass |
| P5 | Baseline BiLSTM training | W2-3 | Model + training log |
| P6 | Model improvements and comparison table | W3-4 | Better held-out accuracy |
| P7 | TF.js export, quantization, `sample_io` | W3-4 | Browser-ready folder |
| P8 | `realtime_demo.py` | W3 | Works on laptop webcam |
| P9 | Evaluation report + model card | W4-5 | Docs with real numbers |
| P+ | Stretch: fingerspelling (A-Z, 0-9); continuous recognition with CTC | W5-6 | Optional |

---

## 11. Commands

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r ml/requirements.txt
python ml/extract_keypoints.py --src data/raw --dst data/processed
python ml/preprocess.py --check
python ml/train.py --classes data/classes.json --data data/processed --meta data/metadata.csv
python ml/evaluate.py --model ml/artifacts/isl_model.keras
bash ml/export_tfjs.sh
python ml/realtime_demo.py --model ml/artifacts/isl_model.keras
pytest ml/tests
```

---

## 12. Things Parth must provide (ask if missing)

- Video data (INCLUDE download and own recordings), signer consent, signer IDs.
- Approval of the vocabulary list.
- Access to a GPU (Colab/Kaggle) if training is slow.

If data is missing, continue with a tiny synthetic stub marked `MOCK` so the pipeline can be tested, and never report results from it as real.

---

## 13. First message to start with

When Parth says "start", reply with:
1. A 10-line summary of your understanding of the ML track.
2. The questions that block P1-P3 (data location, signers, vocabulary).
3. A plan for P1-P4 with the exact files you will create.

Then wait for confirmation before generating code.
