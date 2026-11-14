# ISL Translator: Demo & Presentation Walkthrough Script

> **Time:** 5–7 Minutes  
> **Presenters:** Siddhant (Frontend & Integration) • Parth (Data & ML) • Abhi (NLP & Backend)  
> **Source Problem:** Ministry of Social Justice and Empowerment / ISLRTC / DePWD (2024 Software Track)

---

## 1. One-Line Pitch

> *"An on-device, privacy-first software system that translates Indian Sign Language (ISL) gestures into natural text and speech in multiple Indian languages in real time, enabling deaf and hearing citizens to communicate without an interpreter."*

---

## 2. Presentation Flow & Timing Breakdown

### Segment 1: The Problem (45 Seconds) — [Speaker: Siddhant]
- In India, over 18 million individuals are deaf or hard-of-hearing.
- Only ~300 certified ISL interpreters exist nationwide—a ratio of 1 interpreter for every 60,000 deaf citizens.
- In critical situations (emergency rooms, police desks, banks, transit counters), deaf individuals encounter immediate communication barriers.

### Segment 2: The Solution & Architecture (45 Seconds) — [Speaker: Abhi]
- Show the **System Architecture Pipeline**:
  `Webcam ──► MediaPipe 258-D Vector ──► Invariant Normalization ──► BiLSTM Model ──► NLP SOV Restructuring ──► IndicTrans2/Bhashini ──► Audio Output`
- Point out the 3 core principles:
  1. **Strict On-Device Privacy:** Video never leaves the user's laptop or mobile phone.
  2. **Deterministic Emergency Mode:** High-priority safety gestures bypass generative LLMs completely.
  3. **Zero-Hardware Dependency:** Operates seamlessly on standard commodity cameras.

### Segment 3: Live Interactive Demo (2.5 Minutes) — [Speaker: Siddhant]
| Step | What the Presenter Does | Screen Visual | What Happens Under the Hood |
|---|---|---|---|
| **1** | Open `https://isl-translator.vercel.app`, allow camera. | Green tag: *"Hands detected (30 FPS)"* | MediaPipe Holistic extracts 258-D pose & hand vectors at 30 FPS. |
| **2** | Sign `HELLO` to the camera. | Chip: `Sign: HELLO (94%)` | TensorFlow.js running in Web Worker predicts `HELLO`; 4/5 voting filter commits sign. |
| **3** | Sign `ME`, `HOSPITAL`, `GO`. | Chips: `[ME] [HOSPITAL] [GO]` | Rolling 30-frame sequence buffer updates with 1-second refractory cooldown. |
| **4** | Lower hands for 1.5 seconds. | Status: *"Sentence ready"* | Inactivity pause triggers Next.js proxy call to `POST /api/sentence`. |
| **5** | Automatic translation renders. | **English:** *"I am going to the hospital."*<br/>**Hindi:** *"मैं अस्पताल जा रहा हूँ।"* | Rule-based SOV reordering + IndicTrans2 multilingual translation. |
| **6** | Audio synthesis speaks aloud. | Audio wave animation. | Web Speech API plays native Hindi audio (`hi-IN`). |
| **7** | Tap top-bar **SOS** button or sign `HELP`. | Full-screen red alert, loud alarm. | Emergency bypass triggers deterministic template without generative latency. |
| **8** | Switch to **Two-Way Chat** tab; hearing person clicks *"Mic"* and speaks *"Okay, which doctor?"*. | Live chat bubble appears with text and ISL glosses `[DOCTOR] [WHICH]`. | Web Speech Recognition transcribes audio; `sentence_to_glosses()` generates ISL tokens. |

### Segment 4: Machine Learning & Results (45 Seconds) — [Speaker: Parth]
- **Held-Out Signer Top-1 Accuracy:** **86.4%** on unseen signers `p05` and `p07`.
- **Top-5 Accuracy:** **97.1%**.
- **Vector Normalization Speed:** **0.104 ms** (invariant to distance and camera position).
- **IDLE Rejection:** **98.6%** accuracy suppressing casual non-signing hand fidgets.

### Segment 5: Impact & Roadmap (45 Seconds) — [Speaker: Abhi]
- Partnership with ISLRTC to expand vocabulary to 250+ signs.
- Continuous sequence recognition with Connectionist Temporal Classification (CTC).
- 3D animated signing avatar for complete reverse two-way signing playback.

---

## 3. Demo-Day Safety Checklist

- [ ] Ensure lighting is frontal and even (avoid positioning with an open window directly behind you).
- [ ] Laptop camera positioned at mid-chest to eye level.
- [ ] Verify audio volume is turned up for speech synthesis demo.
- [ ] Pre-warm offline browser cache by visiting the PWA prior to stepping on stage.
- [ ] Keep backup video clip available in `docs/` in the event of local WiFi dropout.

---

## 4. Anticipated Judge Questions & Recommended Answers

**Q1: How does your model handle regional variations in ISL across states?**  
*Answer:* "We strictly adopt the canonical national dictionary published by ISLRTC under the Ministry of Social Justice and Empowerment as our ground truth. In our Phase 5 roadmap, we support regional dialect dictionary packs and few-shot custom sign recording."

**Q2: What happens if the internet goes down during an emergency?**  
*Answer:* "Our core sign recognition model runs 100% on-device in the browser using TensorFlow.js and WebAssembly. Emergency phrases use hard-coded, zero-latency local templates and browser `speechSynthesis`, functioning fully offline with zero cloud dependency."

**Q3: Why did you choose landmark extraction over raw pixel CNNs (like 3D ResNet)?**  
*Answer:* "Raw video models require heavy server GPUs, transmit private facial biometric data over networks, and struggle with background/clothing variations. MediaPipe extracts 258 abstract skeletal landmarks in 2ms, compressing frame bandwidth by 99.8% while guaranteeing complete signer privacy."
