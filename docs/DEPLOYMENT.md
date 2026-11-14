# Deployment preparation

This document describes a deployment target, not a completed deployment. No
production backend or frontend URL is currently verified.

## Architecture target

- Next.js frontend can be deployed separately (for example, on Vercel).
- FastAPI backend can run in the supplied Dockerfile on a Python container host.
- Browser camera access requires HTTPS in production.

## Backend environment

Set environment variables in the hosting provider's secret/configuration store;
do not upload `.env` or commit credentials.

```text
ALLOWED_ORIGINS=https://<your-frontend-host>
RATE_LIMIT_PER_MIN=60
LLM_API_KEY=
LLM_MODEL=gemini-2.5-flash
```

`LLM_API_KEY` is optional. Without it, the backend uses rules and deterministic
fallback. The Gemini model can be overridden with `LLM_MODEL`. Bhashini variables
are not required or used by the current implementation; no cloud translation or
cloud TTS integration is enabled.

See [backend configuration](./BACKEND_CONFIGURATION.md) for all settings.

## Docker

Build from the repository root because the Dockerfile copies backend code and
the data files from the build context:

```bash
docker build -t isl-backend:local -f backend/Dockerfile .
docker run --rm -p 8000:8000 isl-backend:local
```

To pass deployment-provided variables, use the platform's environment settings.
For local development only, `--env-file .env` may be added when `.env` exists.

The container entrypoint is `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
Verify locally with `GET /health`, `GET /docs`, and the backend test suite before
deploying. A successful local/container check is not proof of a real deployment.

## Pre-deployment checklist

- [ ] Configure the exact production frontend origin in `ALLOWED_ORIGINS`.
- [ ] Decide whether optional Gemini processing is appropriate and disclose it.
- [ ] Run `.venv/bin/python -m pytest backend/tests -v`.
- [ ] Verify container startup and `/health` in an environment with Docker.
- [ ] Verify a real deployment URL and health endpoint before advertising it.
- [ ] Confirm Hindi/Marathi browser voices on target devices; browser voice
  availability varies by platform.
- [ ] Obtain ISL-domain-expert review of emergency language and classifications.
