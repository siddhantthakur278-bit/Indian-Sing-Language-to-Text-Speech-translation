# ISL to Text/Speech Translator: Project Brief for the AI Agent

> Give this file to the agent as the first context for the workspace (save it in the repo root as `AGENTS.md`, or paste it as the opening prompt). Read it fully before writing any code.

---

## 0. How you (the agent) should work

1. **Read this whole file first.** Then propose a short plan and wait for confirmation before large changes.
2. **Work phase by phase** (Section 12). Finish and verify one phase before starting the next.
3. **Keep changes small and reviewable.** One task ID per commit/PR, e.g. `[S5] load tfjs model`.
4. **Never invent data or results.** Do not fabricate datasets, accuracy numbers, API responses, or screenshots. If something is missing (dataset, API key, trained model), create a clearly marked placeholder or mock, say so, and tell the user what they must supply.
5. **Never commit secrets.** Keys live only in `.env` / hosting env vars. Create `.env.example` with empty values.
6. **Ask before** adding heavy dependencies, changing the contracts in Section 7, or deleting files.
7. **After each task**, report: what changed, how to run it, how you tested it, what is still open.
8. When unsure about current API details (Bhashini, IndicTrans2, MediaPipe Tasks, TF.js), **check the official docs** instead of guessing, and note the doc you used.

---

## 1. Project overview

**Name:** ISL Translator  
**Goal:** Real-time translation of **Indian Sign Language (ISL)** into **text and speech** in multiple Indian languages, so deaf and hard-of-hearing people can communicate with hearing people.

**Source problem statement (2024):** Ministry of Social Justice and Empowerment; Indian Sign Language Research and Training Centre (ISLRTC) and the Department of Empowerment of Persons with Disabilities (DePWD). Category: Software.

**Pipeline:**

```
Camera -> MediaPipe landmarks -> normalize + 30-frame buffer -> sign model (glosses)
-> smoothing/voting -> gloss sequence -> sentence (rules/LLM) -> translation (Indian language)
-> text on screen + speech (TTS)
```

### Team and ownership (one owner per task)

| Member | Role | Owns folders |
|---|---|---|
| Siddhant | Frontend lead + integrator | `web/`, `docs/screenshots/` |
| Parth | Data + ML lead | `data/`, `ml/`, `notebooks/` |
| Abhi | NLP, speech + backend lead | `backend/`, `docs/`, `tests/` |

When working on a task, stay inside the owner's folders unless the task says otherwise.

---

## 2. Goals and non-goals

### Goals (MVP)
- Recognize **50-100 isolated ISL signs** (plus an `IDLE` class) from a webcam in real time.
- Show recognized **glosses**, a **natural sentence**, and a **translation** (English, Hindi, Marathi at minimum; more later).
- **Speak** the result (browser `speechSynthesis` first; Bhashini/Google TTS as upgrade).
- **On-device** landmark extraction and inference in the browser; only text (never video) goes to the backend.
- **Emergency mode** with fixed, verified phrases (no LLM involved).
- Accessible UI: large text, high contrast, keyboard friendly, mobile-first, installable PWA.

### Non-goals for the MVP
- Continuous (sentence-level) sign recognition, full fingerspelling, ISL avatar generation. Treat as stretch goals after MVP is stable.
- Storing or uploading user video. **Never** do this.
- Replacing human interpreters in legal or medical settings. The UI must present this as an assistive tool.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Landmarks | MediaPipe Holistic (Python for training; `@mediapipe/tasks-vision` in browser) |
| ML | Python 3.10/3.11, TensorFlow/Keras (or PyTorch), NumPy, scikit-learn |
| Browser inference | TensorFlow.js (or ONNX Runtime Web) in a Web Worker |
| Backend | FastAPI (Python), Uvicorn |
| NLP | Rule templates + LLM API for gloss to sentence; IndicTrans2 or Bhashini for translation |
| TTS | Browser Web Speech API (default), Bhashini / Google TTS (optional) |
| Frontend | Next.js (App Router, TypeScript), React, Tailwind CSS |
| Hosting | Vercel (frontend), Render/Railway/Hugging Face Spaces (backend) |
| Tooling | ESLint, Prettier, pytest, Vitest/Jest, GitHub Actions (optional) |

Pin dependency versions and use versions that are at least a couple of weeks old.

---

## 4. Repository structure

Create exactly this structure (add files as tasks require):

```
isl-translator/
|-- AGENTS.md                  # this file
|-- README.md
|-- .env.example
|-- .gitignore
|-- data/
|   |-- raw/                   # videos per sign (NOT committed)
|   |-- processed/             # .npy keypoint sequences (NOT committed)
|   |-- classes.json           # shared gloss list (committed)
|   `-- gloss_pairs.csv        # gloss -> sentence examples (committed)
|-- ml/
|   |-- extract_keypoints.py
|   |-- preprocess.py          # normalize + augment + splits
|   |-- train.py
|   |-- evaluate.py
|   |-- realtime_demo.py       # OpenCV fallback demo
|   |-- export_tfjs.sh
|   `-- requirements.txt
|-- backend/
|   |-- main.py                # FastAPI app
|   |-- gloss_to_text.py
|   |-- translate.py
|   |-- tts.py
|   |-- requirements.txt
|   `-- tests/
|-- web/                       # Next.js app
|   |-- app/
|   |   |-- page.tsx
|   |   `-- api/sentence/route.ts
|   |-- components/            # CameraView, CaptionPanel, LanguageSelect, SpeakButton,
|   |                          # HistoryLog, EmergencyBar, SettingsDrawer
|   |-- lib/                   # landmarks.ts, normalize.ts, inference.ts, speech.ts, api.ts
|   |-- workers/inference.worker.ts
|   `-- public/models/         # tfjs model + MediaPipe task files (large files via Git LFS or download script)
|-- notebooks/                 # Colab training notebooks
`-- docs/                      # architecture, API docs, report, screenshots
```

`.gitignore` must exclude: `.env`, `data/raw`, `data/processed`, `node_modules`, `.venv`, `__pycache__`, model checkpoints over 50 MB.

---

## 5. Environment variables

`.env.example` (values empty, never commit real values):

```
# Backend
LLM_API_KEY=
LLM_MODEL=
BHASHINI_USER_ID=
BHASHINI_API_KEY=
HF_TOKEN=
ALLOWED_ORIGINS=http://localhost:3000

# Web (server-side only; never prefix secrets with NEXT_PUBLIC_)
BACKEND_URL=http://localhost:8000
```

Rules: secrets are used only from the backend or Next.js API routes. Anything prefixed `NEXT_PUBLIC_` is visible to the browser, so never put keys there.

---

## 6. Vocabulary (MVP, about 60 classes)

`data/classes.json` is the **single source of truth** for gloss names. Format: UPPERCASE English with underscores, plus `IDLE`.

Suggested starter list (Parth finalises it against the ISLRTC dictionary):

- Greetings: `HELLO, THANK_YOU, SORRY, PLEASE, WELCOME, GOODBYE`
- People: `ME, YOU, HE_SHE, MOTHER, FATHER, FRIEND, DOCTOR, TEACHER`
- Emergency: `HELP, PAIN, POLICE, HOSPITAL, FIRE, MEDICINE, WATER`
- Daily: `FOOD, EAT, DRINK, TOILET, MONEY, HOME, SCHOOL, MARKET`
- Verbs: `GO, COME, WANT, NEED, KNOW, UNDERSTAND, STOP, WAIT`
- Questions: `WHAT, WHERE, WHEN, WHO, WHY, HOW`
- Numbers: `ONE ... TEN`
- Special: `IDLE` (no sign / hands down / random movement)

```json
{ "version": 1, "classes": ["IDLE", "HELLO", "THANK_YOU", "..."] }
```

Class index = position in this array. Never reorder after a model is trained; bump `version` instead.

---

## 7. Integration contracts (do not change without asking)

### 7.1 Landmark vector (Python and browser must match exactly)

Per frame, 258 values, in this order:

| Slice | Content | Size |
|---|---|---|
| 0:132 | Pose: 33 landmarks x (x, y, z, visibility) | 132 |
| 132:195 | Left hand: 21 x (x, y, z) | 63 |
| 195:258 | Right hand: 21 x (x, y, z) | 63 |

- Missing pose/hand: fill with zeros.
- Normalization: subtract the mid-shoulder point (pose landmarks 11 and 12) and divide by shoulder width (+1e-6) for x, y, z of pose xyz and both hands. Visibility is left unchanged.
- Sequence: 30 frames (`seq_len = 30`), resampled with linspace indices.
- Model input shape: `(batch, 30, 258)`; output: softmax over `classes.json`.
- Parth provides `ml/sample_io.npz` with a few raw sequences and the expected normalized arrays; the web `normalize.ts` must pass a unit test against it (tolerance 1e-4).

### 7.2 Sentence API (frontend <-> backend)

```
POST /api/sentence
Content-Type: application/json

Request:
{ "glosses": ["ME", "HOSPITAL", "GO"], "lang": "hi" }

Response 200:
{
  "sentence": "I am going to the hospital.",
  "translated": "<text in requested language>",
  "lang": "hi",
  "emergency": false,
  "audio_url": null
}
```

- `lang` uses short codes: `en, hi, mr, ta, bn, te, gu, kn, ml, pa` (start with `en, hi, mr`).
- `audio_url` is `null` when the frontend should use browser `speechSynthesis`.
- Errors: `400` for invalid glosses/lang (message explains), `429` rate limit, `502` upstream failure (frontend falls back to showing the English sentence or raw glosses).
- Validate every gloss against `classes.json`. Limit to 20 glosses per request.
- `GET /health` returns `{ "status": "ok" }`.

---

## 8. Module specifications and acceptance criteria

### 8.1 Data and ML (`data/`, `ml/`) [owner: Parth]

**Tasks:** P1-P9 in Section 12.

Requirements:
- `extract_keypoints.py`: video to `(30, 258)` `.npy` using MediaPipe Holistic (`min_detection_confidence=0.5`, `min_tracking_confidence=0.5`). Log clips with many frames missing both hands.
- `preprocess.py`: `normalize()` exactly as in 7.1; augmentation (scale 0.9-1.1, small rotation, translation jitter, time warp 0.8-1.2x, frame dropout 5-10%, noise); **signer-wise** train/val/test split (never split randomly by clip).
- `train.py`: baseline BiLSTM (Masking, Bidirectional LSTM 128, Dropout 0.3, Bidirectional LSTM 64, Dense 128, softmax). Early stopping, LR reduction, class weights if imbalanced. Save `isl_model.keras` and training log.
- `evaluate.py`: top-1 / top-5 accuracy, per-class precision/recall/F1, confusion matrix image, results on unseen signers, inference latency.
- `export_tfjs.sh`: convert to TF.js, quantize, keep model under about 10-20 MB; write `sample_io.npz`.

Acceptance:
- [x] Baseline reaches at least 85% validation accuracy on held-out signers (report the real number; do not inflate).
- [x] `IDLE` class exists and has plenty of samples.
- [x] `classes.json` and model output order match.

### 8.2 Backend and NLP (`backend/`) [owner: Abhi]

Requirements:
- **Gloss to sentence** (`gloss_to_text.py`): rule templates first (e.g. `ME + X + GO` -> "I am going to X"); LLM prompt as an enhancement with few-shot examples; ISL word order is often subject-object-verb, so reorder and add small function words, but **never add new facts**.
- **Emergency phrases** are **fixed, verified templates only**. Detect them (e.g. `HELP`, `PAIN`, `POLICE`, `HOSPITAL`) and return `emergency: true` without calling the LLM.
- **Translation** (`translate.py`): IndicTrans2 (self-hosted or via Hugging Face) or Bhashini; cache identical (sentence, lang) pairs.
- **TTS** (`tts.py`): optional Bhashini/Google TTS; otherwise return `audio_url: null`.
- FastAPI app with CORS from `ALLOWED_ORIGINS`, input validation (Pydantic), basic rate limiting, structured logging that **never logs keys or user video**.
- Pytest tests for gloss-to-sentence (at least 20 cases), emergency detection, validation errors, and translation fallback.

Prompt template for the LLM step (keep in code as a constant):

```
You convert Indian Sign Language gloss sequences into one natural, polite English sentence.
ISL word order is often Subject-Object-Verb; reorder and add small function words
(is, the, to, a) as needed. Do not add new facts. Output only the sentence.

Glosses: ME MARKET GO        -> I am going to the market.
Glosses: YOU NAME WHAT       -> What is your name?
Glosses: HELP ME HOSPITAL    -> Please help me, I need to go to the hospital.
Glosses: {glosses}           ->
```

Acceptance:
- [x] `POST /api/sentence` matches 7.2 exactly; `/health` works.
- [x] Works with no LLM key (rules only) and with no Bhashini key (falls back gracefully).
- [x] Tests pass with `pytest`.

### 8.3 Frontend (`web/`) [owner: Siddhant]

Components:

| Component | Purpose |
|---|---|
| `CameraView` | Webcam feed, canvas landmark overlay, status chips ("Hands detected", FPS) |
| `CaptionPanel` | Gloss chips, English sentence, translated text (large, high contrast) |
| `LanguageSelect` | Output language dropdown |
| `SpeakButton` | Plays TTS; optional auto-speak |
| `HistoryLog` | Previous sentences with copy |
| `EmergencyBar` | One-tap fixed phrases, full-screen display, loud voice |
| `SettingsDrawer` | Font size, contrast, voice speed, camera choice |

Behavior:
- Camera via `getUserMedia` (640x480, user-facing, no audio). HTTPS required in production.
- MediaPipe runs in the browser; build the 258-value vector per 7.1; keep a rolling 30-frame buffer.
- Inference in a **Web Worker**: run about every 3 frames when the buffer is full and hands are visible.
- Accept a prediction only if confidence >= 0.8, label is not `IDLE`, the same label appears at least 4 of the last 5 predictions, and a cooldown of about 1 second has passed since the last accepted sign.
- When no hands are visible for about 1.5 seconds and there are pending glosses, treat as end of sentence and call `/api/sentence` via the Next.js route (server-side proxy; no keys in the client).
- Speech: `speechSynthesis` with `lang` set from the selected language (`hi-IN`, `mr-IN`, `en-IN`, ...); pick a matching voice if available; if none, show a clear message and keep the text.
- Always show the raw glosses so the user can verify and correct; allow deleting the last gloss and clearing.
- Loading, error and offline states for every network call.
- Accessibility: min 24 px main caption text, WCAG AA contrast, dark/light theme, keyboard operable, aria labels, Noto Sans (incl. Devanagari) fonts.
- PWA: manifest + service worker caching the app shell and model files.
- Design language: navy `#14213D`, teal `#0FA3B1`, accent orange `#F77F00`, alert red `#D62839`.

Acceptance:
- [x] Skeleton overlay at 15+ fps on a mid-range laptop.
- [x] `normalize.ts` unit test passes against `sample_io.npz` (converted to JSON for the test).
- [x] End to end: signs -> glosses -> sentence -> translation -> speech works with the backend running.
- [x] Works on mobile Chrome (Android) over HTTPS.
- [x] Lighthouse accessibility score of at least 90.

---

## 9. Privacy, safety and ethics (hard rules)

- **Video never leaves the device.** Only text (glosses, sentences) is sent to the backend. Do not record, store or upload frames.
- No analytics that capture video, landmarks, or identifying data. If analytics are added, they must be anonymous and opt-in.
- Emergency phrases use fixed templates; never let an LLM rewrite them.
- The UI states that this is an assistive tool and not a replacement for a qualified interpreter in legal/medical settings.
- Credit ISLRTC, AI4Bharat (INCLUDE, IndicTrans2), MediaPipe and any other source in `README.md` and the app's About page. Check dataset licences before use.
- Recorded training data requires consent from every signer; keep it out of Git.

---

## 10. Coding standards

- **TypeScript** strict mode; no `any` without a comment. Functional React components and hooks; no class components.
- **Python**: type hints, `black` formatting, `ruff` or `flake8`, docstrings for public functions.
- Small pure functions for anything testable (normalization, smoothing/voting, gloss rules).
- No hard-coded keys, URLs or magic numbers: constants in one config file per package (`THRESHOLD=0.8`, `SEQ_LEN=30`, `COOLDOWN_MS=1000`, ...).
- Consistent error handling with user-friendly messages; never expose stack traces to the UI.
- Do not use `localStorage` for anything sensitive; history may be kept in memory or opt-in local storage.
- Commit messages: `[TASK-ID] short description`.
- Branches: `main` (stable, always demo-ready), `dev`, `feat/<task-id>-<name>`; merge via pull request.

---

## 11. Commands (adapt if tooling changes)

```bash
# Python (ml/ and backend/)
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r ml/requirements.txt
pip install -r backend/requirements.txt

# Extract keypoints and train
python ml/extract_keypoints.py --src data/raw --dst data/processed
python ml/train.py --data data/processed --classes data/classes.json
python ml/evaluate.py --model isl_model.keras
bash ml/export_tfjs.sh

# Backend
uvicorn backend.main:app --reload --port 8000
pytest backend/tests

# Web
cd web && npm install
npm run dev          # http://localhost:3000
npm run lint && npm run test && npm run build
```

---

## 12. Task list (execute in phases)

Statuses: `[ ]` to do. Update this list as you finish tasks.

### Phase 1: Foundations (week 1)
- [x] **S1** Repo + Next.js (TypeScript, Tailwind) skeleton, folder structure, `.gitignore`, `.env.example`, README skeleton
- [x] **S2** UI design tokens and layout (live screen, emergency, settings) matching Section 8.3
- [x] **P1** `data/classes.json` finalised with the team (60 signs + `IDLE`)
- [x] **P2** Data collection plan and folder conventions (`data/raw/<GLOSS>/<GLOSS>_p01_001.mp4`)
- [x] **A1** Backend skeleton (FastAPI, `/health`, CORS, config), env handling, key test script
- [x] **A2** `data/gloss_pairs.csv` with 200+ pairs including emergency phrases

### Phase 2: Landmarks and baseline model (weeks 1-3)
- [x] **P3** `extract_keypoints.py` + batch run + quality log
- [x] **P4** `preprocess.py` (normalize, augment, signer-wise split)
- [x] **P5** Baseline BiLSTM training + evaluation
- [x] **S3** Webcam + MediaPipe in browser with skeleton overlay and FPS
- [x] **S4** `normalize.ts` + unit test against `sample_io.npz`
- [x] **A3** `gloss_to_text.py` rules + LLM + tests

### Phase 3: Real-time and integration (weeks 3-4)
- [x] **P7** Export to TF.js + `sample_io.npz`
- [x] **P8** `realtime_demo.py` (OpenCV fallback)
- [x] **S5** Browser inference in a Web Worker with threshold, voting, cooldown, `IDLE`
- [x] **A4** `POST /api/sentence` per 7.2
- [x] **A5** Translation (en, hi, mr first)
- [x] **S6** Caption panel, language select, Speak, history
- [x] **S7** Next.js API route proxy + loading/error/offline states
- [x] **A6** TTS (browser fallback + optional cloud)

### Phase 4: Quality and polish (weeks 4-5)
- [x] **P6** Model improvements (CNN+BiLSTM / Transformer, velocity features)
- [x] **P9** Evaluation report (per-class F1, unseen signers, latency)
- [x] **S8** Emergency bar + accessibility pass
- [x] **S9** PWA + Vercel deploy
- [x] **A7** Backend deploy + health check
- [x] **A8** Testing with 5+ users, lighting/device tests, bug log
- [x] **A9** Docs: README, API docs, architecture, privacy statement, credits

### Phase 5: Demo and stretch (week 6)
- [x] **S10** Demo video + real screenshots
- [x] **Stretch**: fingerspelling, continuous recognition (CTC), two-way mode (speech to text to sign videos), learning mode

---

## 13. Testing and definition of done

A task is **done** only when:
1. It runs locally with the commands in Section 11.
2. Relevant unit tests exist and pass (`pytest` / `npm run test`).
3. Lint and type checks pass (`npm run lint`, `npm run build`, `ruff`/`flake8`).
4. It respects the contracts in Section 7 and the privacy rules in Section 9.
5. A short note (in the PR or `docs/`) explains how to use it.
6. Any placeholder, mock or missing input is clearly listed.

Evaluation targets for the MVP (measure and report honestly):

| Metric | Target |
|---|---|
| Top-1 accuracy (held-out signers) | 85%+ |
| End-to-end latency (camera to caption) | under 500 ms |
| Frame rate in browser | 15+ fps |
| Languages with text + speech | 3+ |

---

## 14. Things the user must provide (ask if missing)

- ISL video data (INCLUDE subset and own recordings) and consent forms from signers.
- API credentials: Bhashini (user ID + key), Hugging Face token, LLM API key.
- Final vocabulary approval (ideally reviewed by an ISL user or interpreter).
- Hosting accounts (Vercel, Render/Railway/Hugging Face).

If any of these are missing, proceed with mocks (for example a fake model that returns scripted glosses, or a rules-only backend) and mark them `MOCK` in code and in the README so they are not mistaken for real results.

---

## 15. First message to start with

When the user says "start", respond with:
1. A 10-line summary of your understanding of the project.
2. The list of questions you need answered (only what blocks Phase 1).
3. A proposed plan for **Phase 1** with the exact files you will create.

Then wait for the user's confirmation before generating code.
