# ISL Gesture Recognition Model Card

This Model Card documents the architecture, input/output tensor specifications, preprocessing contracts, performance metrics, and operational limitations for the Indian Sign Language (ISL) gesture recognition neural network.

---

## 1. Model Overview

- **Model Type**: Deep Neural Network for Isolated Sign Language Recognition
- **Supported Architectures**:
  - **Baseline**: Bidirectional LSTM (BiLSTM with zero-masking)
  - **Hybrid**: 1D Temporal CNN + BiLSTM
  - **Transformer**: Lightweight Self-Attention Encoder
- **Framework**: TensorFlow / Keras (exported to TensorFlow.js float16/int8)
- **Target Runtime**: Browser client-side inference via Web Worker (`@tensorflow/tfjs`) with Python OpenCV fallback (`ml/realtime_demo.py`)
- **Single Source of Truth**: [`ml/config.py`](file:///Users/parthnayak/Code/Projects_code/Group/Indian-Sing-Language-to-Text-Speech-translation/ml/config.py) and [`data/classes.json`](file:///Users/parthnayak/Code/Projects_code/Group/Indian-Sing-Language-to-Text-Speech-translation/data/classes.json)

---

## 2. Input Tensor Specification (Contract 7.1)

| Property | Value | Notes |
|---|---|---|
| **Tensor Name** | `seq_input` / `landmark_input` | Input layer identifier in Keras / TF.js graph |
| **Shape** | `(batch, 30, 258)` | Resampled fixed window of 30 temporal frames |
| **Data Type** | `float32` | Normalized coordinates |
| **Sequence Length** | `30` | Linear-space temporal resampling (`np.linspace(0, T-1, 30)`) |
| **Feature Dimension** | `258` | Pose, left hand, and right hand keypoints |

### Feature Slices Breakdown

```
Index Range      Landmark Source    Elements    Description
-----------------------------------------------------------------------------------
[0:132]          Pose Landmarks     33 x 4      33 points x (x, y, z, visibility)
[132:195]        Left Hand          21 x 3      21 points x (x, y, z)
[195:258]        Right Hand         21 x 3      21 points x (x, y, z)
```

### Preprocessing & Normalization Protocol
1. **Shoulder Midpoint Translation**:
   $$\text{center} = \frac{\text{landmark}_{11} + \text{landmark}_{12}}{2}$$
   Translates pose and hand $(x, y, z)$ coordinates such that mid-shoulder is positioned at $(0, 0, 0)$.
2. **Torso Scale Invariance**:
   $$\text{scale} = \|\text{landmark}_{11} - \text{landmark}_{12}\|_2 + 10^{-6}$$
   Divides coordinates by Euclidean distance between shoulders, scaling torso width to approximately $1.0$.
3. **Visibility Preservation**: Pose visibility values ($v$) remain unscaled in range $[0.0, 1.0]$.
4. **Absent Hand Handling**: Absent hands are initialized with $0.0$. If hand magnitude is $< 10^{-5}$, hand landmark slices strictly preserve $0.0$ to avoid numerical artifacts or false coordinates.

---

## 3. Output Tensor Specification

| Property | Value | Notes |
|---|---|---|
| **Tensor Name** | `class_probabilities` / `gloss_output` | Final softmax probability output |
| **Shape** | `(batch, 70)` | Matches vocabulary count in `data/classes.json` |
| **Data Type** | `float32` | Probabilities summing to 1.0 across classes |
| **Class Indexing** | `0` to `69` | Exact positional index in `data/classes.json` array |
| **Special Class** | `IDLE` (Index `0`) | Neutral posture, resting hands, non-signing activity |

---

## 4. Runtime Inference Thresholds & State Machine

Predictions are filtered through a temporal smoothing state machine in both the browser Web Worker and the Python demo:

- **Confidence Threshold**: $\ge 0.80$ (predictions with probability below 0.80 are discarded as uncertain)
- **Temporal Voting Window**: $5$ consecutive frames
- **Consensus Requirement**: $\ge 4$ out of $5$ predictions must agree on the same gloss
- **Refractory Cooldown**: $30$ frames ($\sim 1.0$ s at 30 fps) before committing a subsequent sign
- **Sentence Commit Inactivity**: $1500$ ms with no active hands triggers the NLP sentence translation API

---

## 5. Intended Use & Assistive Scope

- **Primary Application**: Two-way assistive communication enabling Deaf and Hard-of-Hearing individuals to convey ISL signs converted to natural English sentences, Indian language translations, and synthetic speech.
- **Safety Boundary**: This tool is an assistive aid. It is **not** certified to replace qualified, professional human sign language interpreters in legal, judicial, medical, or diagnostic environments.

---

## 6. Privacy & Ethics

- **Zero Video Transmission**: Camera frames never leave the user's client device. Landmark extraction and neural network inference execute entirely client-side. Only recognized text glosses are sent to backend translation routes.
- **Data Protection**: Training data recordings require explicit signer consent and are kept outside Git version control.

---

## 7. Known Limitations

- **Lighting & Occlusion**: Extreme backlighting or poor contrast may cause MediaPipe hand landmark tracking drops.
- **Continuous Signing**: The MVP model is calibrated for isolated sign recognition. Fast continuous sentences without neutral transitions between signs require future CTC/encoder-decoder upgrades.
- **Regional Dialects**: Indian Sign Language exhibits regional variations across India; signs are aligned with ISLRTC standard definitions.
