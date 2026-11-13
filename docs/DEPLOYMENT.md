# Deployment Runbook & Production Operations

> **Owners:** Siddhant (Frontend & Integrator) • Abhi (Backend & Speech)

---

## 1. Production Architecture Overview

The system is deployed using a decoupled jamstack architecture:
- **Frontend App:** Next.js 14 hosted on **Vercel** edge network.
- **Backend Service:** FastAPI Python service hosted on **Render / Railway / Hugging Face Spaces**.
- **Static Model Files:** TensorFlow.js graph model served via CDN or public asset cache.

---

## 2. Frontend Deployment (Vercel)

### Crucial Requirement: HTTPS
Browser webcam access via `navigator.mediaDevices.getUserMedia` **mandates HTTPS**. Vercel provides automatic SSL certificates for all preview and production deployments.

### Steps:
1. Link your GitHub repository in the [Vercel Dashboard](https://vercel.com).
2. Set the **Root Directory** to `web`.
3. Configure Environment Variables:
   - `BACKEND_URL`: URL of the deployed FastAPI backend (e.g. `https://isl-api.onrender.com`).
4. Trigger Build:
   - Framework preset: `Next.js`
   - Build command: `npm run build`
   - Output directory: `.next`

---

## 3. Backend Deployment (Render / Railway / Docker)

### Environment Variables (.env):
```bash
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
LLM_API_KEY=your_optional_llm_key
BHASHINI_USER_ID=your_bhashini_id
BHASHINI_API_KEY=your_bhashini_key
```

### Docker Startup:
```bash
docker build -t isl-backend:latest -f backend/Dockerfile .
docker run -p 8000:8000 --env-file .env isl-backend:latest
```

---

## 4. Verification Checklist Before Launch

- [ ] `GET /health` returns `{"status": "ok"}` on production URL.
- [ ] Emergency phrases return `emergency: true` without timeout.
- [ ] Camera stream renders skeleton overlay at 15+ FPS on mid-range Android phone.
- [ ] Browser `speechSynthesis` voices load properly in Hindi and Marathi.
- [ ] PWA installs successfully to device home screen.
