# Backend test report

This report distinguishes automated software checks from real-world evaluation.

## Automated checks

Run the backend suite from the repository root:

```bash
.venv/bin/python -m pytest backend/tests -v
```

The suite covers API contracts and validation, vocabulary validation, emergency
priority and LLM bypass, Gemini request handling using mocks, bounded caches,
rate limiting, offline translation lookup, TTS locale mappings, and glossary
CSV schema/vocabulary checks. Provider network requests are mocked in tests.

Verification run on 2026-11-14:

```text
143 passed, 0 failed, 1 warning
```

The warning is Starlette's deprecation notice about using `httpx` with
`starlette.testclient`. Automated translation checks validate CSV structure and
script, not linguistic quality.

The package import succeeded. A local Uvicorn smoke check returned HTTP 200 from
`/docs`, and valid responses from `/health`, `/api/sentence`, and
`/api/text-to-gloss`.

The Docker build could not be verified because the local Docker daemon was not
available. No production deployment URL has been verified.

Additional import check:

```bash
.venv/bin/python -c "import backend.main; print('Backend import successful')"
```

## Not evaluated

- No real Gemini request was made; no Gemini key is configured in this
  environment.
- No Bhashini translation or cloud TTS request was made. These providers are not
  implemented in the current backend.
- No deployment or production URL has been verified.
- No real-user testing, interpreter review, or language-quality evaluation is
  represented by the automated tests.
