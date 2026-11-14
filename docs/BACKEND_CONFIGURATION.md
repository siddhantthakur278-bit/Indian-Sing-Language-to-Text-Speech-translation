# Backend configuration

The backend reads a repository-root `.env` file when present and otherwise uses
process environment variables. Copy `.env.example` to `.env` for local work;
never commit `.env` or paste secret values into issue trackers.

| Variable | Required | Default | Current behavior |
|---|---:|---|---|
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origin list |
| `RATE_LIMIT_PER_MIN` | No | `60` | Per direct client peer, shared by POST endpoints |
| `LLM_API_KEY` | No | Empty | Enables the optional Gemini sentence enhancement |
| `LLM_MODEL` | No | `gemini-2.5-flash` | Gemini model used by the REST adapter |
| `BHASHINI_USER_ID` | No | Empty | Reserved; no Bhashini provider is wired |
| `BHASHINI_API_KEY` | No | Empty | Reserved; no Bhashini provider is wired |
| `HF_TOKEN` | No | Empty | Reserved; not used by the current API |

No credential is required to start the backend. Without `LLM_API_KEY`, glosses
are handled by exact templates, emergency rules, ordinary heuristics, and safe
fallback. If Gemini is configured, only non-emergency gloss sequences without
an exact/rule result may be sent to Google's Gemini API.

Translation uses the committed Hindi/Marathi CSV lookup and returns the English
source text when there is no offline pair. Cloud translation is not implemented.
Cloud TTS is not implemented; `audio_url` remains `null`, and the frontend should
use browser `speechSynthesis`.

Run from the repository root:

```bash
uvicorn backend.main:app --reload --port 8000
```

The Gemini adapter calls the documented `generateContent` REST method with the
API key in `x-goog-api-key`, not in the URL. It uses a 10-second timeout and
returns to deterministic local behavior for missing credentials, transport
errors, blocked/incomplete output, or invalid output. Candidate content words
must be licensed by at least one source gloss; if a source gloss has no
grounding mapping or the candidate introduces an unsupported word, the candidate
is discarded and deterministic local behavior is used.

References checked for adapter formats:

- [Google Gemini `generateContent` REST reference](https://ai.google.dev/api/generate-content)
- [Bhashini API overview](https://bhashini.gitbook.io/bhashini-apis/overall-understanding-of-the-api-calls)
- [Bhashini pipeline compute call](https://bhashini.gitbook.io/bhashini-apis/pipeline-compute-call)
