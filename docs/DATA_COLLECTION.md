# Indian Sign Language (ISL) Data Collection & Ethics Protocol

> **Lead Owner:** Parth (Data & ML Lead)  
> **Alignment:** ISLRTC Standard Vocabulary & Ethical Human Biometrics Guidelines

---

## 1. Overview & Objective

To train a robust sequence recognition model (BiLSTM / 1D-CNN) that generalizes well to unseen signers across India, we must collect diverse, high-quality video recordings of isolated signs under varied real-world conditions.

This document details the recording protocols, environment variables, directory conventions, and human signer consent guidelines.

---

## 2. Directory & File Naming Conventions

All raw video files must be placed strictly inside `data/raw/` in per-class subdirectories. Raw video files are **never committed to Git**.

### Folder Hierarchy:
```
data/raw/
├── HELLO/
│   ├── HELLO_p01_001.mp4
│   ├── HELLO_p01_002.mp4
│   └── HELLO_p02_001.mp4
├── HOSPITAL/
│   ├── HOSPITAL_p01_001.mp4
│   └── HOSPITAL_p03_001.mp4
└── IDLE/
    ├── IDLE_p01_001.mp4
    └── IDLE_p02_001.mp4
```

### Naming Syntax:
```
<GLOSS>_p<SIGNER_ID>_<CLIP_INDEX>.mp4
```
- `<GLOSS>`: Exact uppercase name matching `data/classes.json` (e.g. `HELLO`, `THANK_YOU`, `WATER`).
- `p<SIGNER_ID>`: Two-digit zero-padded signer ID (`p01`, `p02`, ..., `p10`).
- `<CLIP_INDEX>`: Three-digit zero-padded clip index (`001`, `002`, ..., `050`).

---

## 3. Recording Technical Specifications

| Parameter | Required Value | Rationale |
|---|---|---|
| **Framerate** | Constant 30 FPS | Matches MediaPipe tracking frequency & real-time browser camera stream |
| **Resolution** | 640 × 480 or 1280 × 720 | High resolution slows landmark extraction without improving spatial accuracy |
| **Duration** | 2.0 to 3.5 seconds per sign | Captures pre-sign rest, full gesture trajectory, and return to rest |
| **Camera Angle** | Frontal eye-level to chest-level | Replicates standard laptop webcam / phone video call perspective |
| **Signer Framing** | Mid-torso to head visible | Ensures shoulders (landmarks 11, 12) and full hand reach remain in frame |

---

## 4. Diversity & Environmental Matrix

Each sign must be recorded across multiple settings:
1. **Lighting Variations:**
   - Bright natural daylight
   - Standard indoor fluorescent / LED tube light
   - Low / dim ambient evening lighting
   - Backlit / side-lit window conditions
2. **Backgrounds:**
   - Plain monochrome wall
   - Cluttered domestic / office background
3. **Signer Characteristics:**
   - 3 to 5 distinct signers minimum
   - Varied hand sizes, skin tones, and arm lengths
   - Left-handed and right-handed dominant signers
   - Clothing variations: short sleeves, long sleeves, watches, bracelets

---

## 5. The Critical `IDLE` Class

The `IDLE` class is essential to prevent false-positive predictions when the signer is at rest or moving naturally:
- Signer sitting relaxed with hands down on lap.
- Adjusting spectacles, collar, or hair.
- Casual non-signing gestures, shifting sitting position.
- Transitional hand rising and lowering.
- **Quota:** At least 100 clips of diverse `IDLE` motions.

---

## 6. Informed Signer Consent Form Template

All human participants must sign an informed consent agreement prior to recording:

```text
================================================================================
INFORMED BIOMETRIC DATA COLLECTION CONSENT FORM
Project: Indian Sign Language (ISL) Assistive Translation Technology
Institution / Department: Ministry of Social Justice and Empowerment / Partner Lab
================================================================================

Participant ID: ______________________ Date: ______________________
Age / Gender:   ______________________ Primary Language: ________________

1. PURPOSE:
   I understand that my video recordings will be used solely for the training and
   benchmarking of machine learning models recognizing Indian Sign Language gestures.

2. PRIVACY & ANONYMIZATION:
   I understand that raw video recordings will be converted into abstract numeric
   landmark coordinates (skeletal joint positions) and will NOT be uploaded to
   public websites, shared with unverified commercial third parties, or used for
   facial recognition.

3. VOLUNTARY PARTICIPATION:
   I participate voluntarily and may request the removal of my clips prior to the
   final model release.

Signer Signature: ___________________________ Date: ______________________
Researcher Signature: _______________________ Date: ______________________
================================================================================
```

---

## 7. Character-Level Fingerspelling Dataset Pipeline

For static character and digit recognition (A–Z and 1–9), the repository ingests the **Prathum Arikeri ISL Character Dataset**:

* **Location:** `data/raw/fingerspelling/` (Excluded from Git per Privacy Contract)
* **Structure:** 35 subdirectories (`A` through `Z` and `1` through `9`), containing 42,745 JPEG images.
* **Manifest:** Evaluated and tracked in `data/fingerspelling_manifest.json`.
* **Automated Setup Script:**
  ```bash
  bash scripts/setup_fingerspelling_dataset.sh
  ```
* **Processing Target:** Converted via dual-hand MediaPipe feature extraction into `data/processed/landmark_dataset_with_orientation.csv` (126-D wrist & MCP scaled feature vectors) for TensorFlow.js browser training.

