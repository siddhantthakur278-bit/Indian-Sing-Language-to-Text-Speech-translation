# Backend API reference

The local development base URL is `http://localhost:8000`. Configure CORS
origins with `ALLOWED_ORIGINS`. No production API URL is currently verified.
All requests and responses use JSON unless noted.

The backend accepts symbolic text only. Never send camera video, frames,
landmarks, or other biometric input to these endpoints.

## `GET /health`

Returns liveness and the configured feature modes. Credentials are never
included in the response.

```json
{
  "status": "ok",
  "features": {
    "gloss_to_sentence": "rules_only",
    "translation": "offline_csv_with_english_fallback",
    "tts": {
      "mode": "browser_speech_synthesis",
      "cloud_available": false,
      "supported_languages": ["bn", "en", "gu", "hi", "kn", "ml", "mr", "pa", "ta", "te"]
    }
  }
}
```

`gloss_to_sentence` is `rules_only` when no `LLM_API_KEY` is configured and
`rules_with_gemini` when configured. Emergency input always bypasses Gemini.
Translation is the committed offline CSV lookup followed by English fallback;
cloud translation is not enabled. TTS is browser-based; cloud TTS is not enabled.

## `POST /api/sentence`

Converts an ISL gloss sequence to English, looks up a Hindi/Marathi translation
when available, and returns an optional cloud-audio URL (`null` in the current
implementation).

Request:

```json
{
  "glosses": ["HELP"],
  "lang": "en"
}
```

`glosses` must contain 1–20 strings. Every gloss is normalized for surrounding
whitespace and case, then validated against `data/classes.json`. Unknown glosses
and `IDLE` return HTTP 400 before downstream processing. `lang` defaults to
`en` and must be one of `en`, `hi`, `mr`, `ta`, `bn`, `te`, `gu`, `kn`, `ml`,
or `pa`.

Successful response (200):

```json
{
  "sentence": "Please help me.",
  "translated": "Please help me.",
  "lang": "en",
  "emergency": true,
  "audio_url": null
}
```

The response fields are `sentence`, `translated`, `lang`, `emergency`, and
`audio_url`. `translated` is the English source when an offline translation is
unavailable. Emergency classification and wording are assistive output and
require domain review; the service is not an emergency-response service.

## `POST /api/text-to-gloss`

Maps supported English words to a gloss sequence for the two-way UI. This is a
rule-based mapping, not a general English-to-ISL translator.

Request:

```json
{"text": "I am going to the hospital"}
```

`text` is limited to 200 characters.

Response (200):

```json
{
  "original_text": "I am going to the hospital",
  "glosses": ["ME", "HOSPITAL", "GO"]
}
```

## Errors and limits

| Status | Meaning | Response |
|---|---|---|
| 400 | Unknown glosses or `IDLE` in sentence input | `{"message": "..."}` |
| 422 | Request schema or unsupported language validation failed | FastAPI validation details |
| 429 | Per-client request limit exceeded | `{"message": "Rate limit exceeded. Maximum N requests per minute."}` |
| 502 | A translation adapter reports an upstream provider failure | `{"message": "Translation service is unavailable."}` |

`RATE_LIMIT_PER_MIN` defaults to 60 and is applied across both POST endpoints.
Client identity uses the direct ASGI peer address; arbitrary
`X-Forwarded-For` values are ignored. HTTP 429 responses include a
`Retry-After` header in seconds, calculated from the earliest request expiry in
the current sliding window. In-memory rate-limit and cache state is per process
and resets on restart.
