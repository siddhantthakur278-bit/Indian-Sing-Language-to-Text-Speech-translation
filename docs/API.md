# ISL Translator Backend REST API Reference

> **Base URL:** `http://localhost:8000` (Local) / `https://api.isl-translator.org` (Production)  
> **Protocol:** HTTP/1.1 & HTTP/2 over TLS/HTTPS  
> **Format:** JSON (`application/json; charset=utf-8`)

---

## 1. Authentication & Security

- Client applications must communicate with the backend exclusively through server-side proxies (e.g. Next.js API Route) or signed headers.
- **Privacy Assurance:** Video streams and raw camera frames are **strictly prohibited** from being sent to this API. Only processed symbolic strings (glosses) are received.

---

## 2. Endpoints

### 2.1 Health Probe
Checks the liveness and readiness of the translation service.

```http
GET /health
```

#### Response (200 OK):
```json
{
  "status": "ok"
}
```

---

### 2.2 Gloss Sequence Translation
Transforms an array of ISL gloss tokens into a natural sentence, performs target language translation, and evaluates emergency safety flags.

```http
POST /api/sentence
Content-Type: application/json
```

#### Request Schema:
| Field | Type | Required | Description | Constraints |
|---|---|---|---|---|
| `glosses` | `List[string]` | **Yes** | Array of recognized uppercase gloss strings | 1 to 20 tokens |
| `lang` | `string` | No | Target ISO language short code (default: `"en"`) | Must be supported code |

#### Supported Language Codes:
`en` (English), `hi` (Hindi), `mr` (Marathi), `ta` (Tamil), `bn` (Bengali), `te` (Telugu), `gu` (Gujarati), `kn` (Kannada), `ml` (Malayalam), `pa` (Punjabi).

#### Example Request:
```json
{
  "glosses": ["ME", "HOSPITAL", "GO"],
  "lang": "hi"
}
```

#### Response Schema (200 OK):
```json
{
  "sentence": "I am going to the hospital.",
  "translated": "मैं अस्पताल जा रहा हूँ।",
  "lang": "hi",
  "emergency": false,
  "audio_url": null
}
```

#### Emergency Trigger Example:
```json
{
  "glosses": ["HELP", "PAIN"],
  "lang": "mr"
}
```

#### Response (200 OK):
```json
{
  "sentence": "Please help me, I am in severe pain.",
  "translated": "कृपया मला मदत करा, मला खूप वेदना होत आहेत.",
  "lang": "mr",
  "emergency": true,
  "audio_url": null
}
```

---

## 3. Error Responses

| HTTP Status | Reason | Schema / Action |
|---|---|---|
| **400 Bad Request** | Empty glosses or invalid token structure | `{"message": "Glosses list cannot be empty."}` |
| **422 Unprocessable Entity** | Unsupported language code or schema failure | Pydantic validation error details |
| **429 Too Many Requests** | Rate limit exceeded (> 60 requests/min per IP) | `{"message": "Rate limit exceeded. Please back off."}` |
| **502 Bad Gateway** | Upstream translation service unreachable | Frontend falls back to cached translation or English sentence |
