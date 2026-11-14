# Indian Sign Language Dataset Documentation & Provenance

> **Lead Owner:** Parth (Data & ML Lead)  
> **Standard:** ISLRTC Official Dictionary Alignment & AI4Bharat INCLUDE Research

---

## 1. Overview & Data Provenance

This dataset comprises isolated Indian Sign Language (ISL) gesture sequences formatted into standardized **30-frame, 258-dimensional landmark vectors**.

The vocabulary is aligned directly with the **Indian Sign Language Research and Training Centre (ISLRTC)** standard reference dictionary under the Ministry of Social Justice and Empowerment (MoSJE), Department of Empowerment of Persons with Disabilities (DePWD).

### Dataset Components:
1. **Public Benchmark (INCLUDE Subset):**
   - Source: AI4Bharat / IIT Madras (INCLUDE: A Large Scale Dataset for Indian Sign Language Recognition, ACM Multimedia 2020).
   - Subset: Classes matching our 70-class canonical list (`data/classes.json`).
2. **Recorded Primary Data:**
   - Multi-signer isolated recordings captured across 8 distinct signers (`p01` through `p08`).
   - Varied lighting (natural daylight, indoor LED, dim, backlit) and backgrounds.
3. **The `IDLE` Negative Class:**
   - At least 100 clips of non-signing resting states, natural conversational arm fidgets, scratching, glasses adjusting, and transitional hand drops.
   - Crucial to suppress false activations in real-time inference.

---

## 2. Partitioning Strategy (Strict Signer-Wise Split)

To ensure true generalization to unseen signers and avoid identity leakage:
* **Train Split (`train`):** Signers `p01`, `p02`, `p03`, `p04`, `p05` (~70% of data).
* **Validation Split (`val`):** Signer `p06` (~15% of data).
* **Test Split (`test`):** Signers `p07` and `p08` (~15% of data, completely held-out).

All clip assignments are cataloged in [`data/metadata.csv`](metadata.csv).

---

## 3. Storage & Privacy Policies

* **Raw Video Files (`data/raw/`):**
  - **Strictly excluded from Git** via `.gitignore`.
  - Stored securely in encrypted cloud object storage (Google Drive / S3).
* **Processed Sequences (`data/processed/`):**
  - Stored as binary `.npy` arrays with shape `(30, 258)`.
  - Non-identifiable abstract skeletal coordinates; zero facial pixels or skin textures preserved.
* **Consent & Ethics:**
  - Formal informed consent obtained from all participating human signers per [`docs/DATA_COLLECTION.md`](../docs/DATA_COLLECTION.md).
