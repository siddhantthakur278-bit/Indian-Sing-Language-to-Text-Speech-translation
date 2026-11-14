# ISL Fingerspelling & Number Classifier

This module implements **real-time character-level fingerspelling recognition** for Indian Sign Language (ISL), enabling users to spell names, acronyms, and unfamiliar words letter-by-letter.

---

## 1. Dataset & Origins

* **Source:** [Indian Sign Language (ISL) Character-Level Dataset](https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl) by **Prathum Arikeri** (Kaggle / Stanford assistance).
* **Licence:** Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0).
* **Classes:** 36 classes total:
  * Alphabet: `A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z` (26 letters)
  * Digits: `1, 2, 3, 4, 5, 6, 7, 8, 9` (9 numerals)
  * Special: `IDLE` (resting hand / no gesture)
* **Dataset Size:** 41,930 real samples extracted with MediaPipe Hands into `data/processed/landmark_dataset_with_orientation.csv`.

---

## 2. Feature Extraction & Normalization

The feature vector consists of **126 floating-point values** representing dual-hand MediaPipe coordinates:

| Slice | Features | Count | Description |
|---|---|---|---|
| `0:63` | Hand 1 (Dominant Hand) | 63 | 21 landmarks $\times$ $(x, y, z)$ |
| `63:126` | Hand 2 (Secondary Hand) | 63 | 21 landmarks $\times$ $(x, y, z)$ (filled with zeros if single-hand sign) |

### Hand Normalization Contract
1. **Wrist Origin:** Hand wrist landmark (landmark 0) is subtracted from all 21 points so the wrist sits at $(0, 0, 0)$.
2. **MCP Scaling:** The scale is the Euclidean distance between the wrist ($lm_0$) and the middle finger MCP knuckle ($lm_9$):
   $$\text{scale} = \sqrt{(x_9 - x_0)^2 + (y_9 - y_0)^2 + (z_9 - z_0)^2} + 10^{-6}$$
3. **Normalized Coordinates:**
   $$(x_{\text{norm}}, y_{\text{norm}}, z_{\text{norm}}) = \frac{(x - x_0, y - y_0, z - z_0)}{\text{scale}}$$

---

## 3. Model Architecture & Performance

* **Architecture:** Multi-Layer Perceptron (MLP) with Batch Normalization:
  * Input Layer: `[126]`
  * Dense 256 (ReLU) + BatchNorm + Dropout (0.25)
  * Dense 128 (ReLU) + BatchNorm + Dropout (0.20)
  * Dense 64 (ReLU) + BatchNorm
  * Dense 36 (Softmax)
* **Model Size:** 311 KB (`web/public/models/group1-shard1of1.bin` + `model.json`).
* **Validation Accuracy:** **99.83%** on held-out test split.
* **Inference Latency:** **< 8 ms** on-device in Web Worker / browser TensorFlow.js.

---

## 4. Real-Time Camera Fingerspelling Studio

* **Location in Web App:** Under the **"🔤 Spell" (Fingerspelling)** tab (`web/components/Fingerspelling.tsx`).
* **Interactive Features:**
  * **Start Live Spell Camera:** Turns on user webcam with live MediaPipe skeletal overlay.
  * **Stability Ring:** Holding a sign steady for $\approx 0.6\text{s}$ ($\ge 8$ consistent frames) automatically commits the character into the active word buffer.
  * **Word Manipulation:** Includes Backspace, Space, Clear, and real-time character count.
  * **Speech Playback:** "Speak Word" button reads out the spelled name/word via browser Speech Synthesis.
  * **ISL Handbook Reference Cards:** Clickable A-Z and 1-9 matrix with step-by-step posture guides verified per ISLRTC handbook.
