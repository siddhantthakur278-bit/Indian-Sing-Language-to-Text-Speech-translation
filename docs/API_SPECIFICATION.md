# ISL Translator: REST API Specification

This document details the REST API routes exposed by the Next.js application server.

---

## 1. User & Statistics API (`/api/user`)

### `GET /api/user`
Retrieves the active user profile, application preferences, and usage metrics from the database.

**Response `200 OK`:**
```json
{
  "user": {
    "id": "cmwgi448v00006aw0hqll98c3",
    "name": "Siddhant",
    "email": "siddhant@isl-translator.org",
    "role": "Signer",
    "preferredLang": "hi",
    "speechRate": 1.0,
    "autoSpeak": true,
    "signMode": "auto",
    "theme": "galaxy-gold"
  },
  "stats": {
    "totalTranslations": 12,
    "savedPhrases": 8,
    "practiceSessions": 4
  }
}
```

### `PATCH /api/user`
Updates user preferences and settings.

**Request Body:**
```json
{
  "name": "Siddhant",
  "role": "Signer",
  "preferredLang": "hi",
  "theme": "galaxy-gold"
}
```

---

## 2. Translation History API (`/api/history`)

### `GET /api/history`
Fetches the last 50 translation history items recorded in the database.

### `POST /api/history`
Saves a new translated sentence record to the database.

**Request Body:**
```json
{
  "glosses": ["HELLO", "FRIEND"],
  "english": "Hello, friend.",
  "translated": "नमस्ते दोस्त।",
  "lang": "hi",
  "isEmergency": false
}
```

### `DELETE /api/history`
Clears all saved translation history records for the current user.

---

## 3. Saved Bookmark Phrases API (`/api/saved-phrases`)

### `GET /api/saved-phrases`
Returns all bookmarked quick phrases for rapid access.

### `POST /api/saved-phrases`
Creates a new custom bookmark phrase in the database.

**Request Body:**
```json
{
  "title": "Need Doctor",
  "glosses": ["DOCTOR", "NEED"],
  "english": "I need to see a doctor.",
  "translated": "मुझे डॉक्टर से मिलना है।",
  "category": "Medical",
  "shortcut": "D"
}
```

### `DELETE /api/saved-phrases?id=<phraseId>`
Deletes a bookmark phrase by ID.

---

## 4. Practice Drills API (`/api/practice`)

### `GET /api/practice`
Fetches recent practice sessions and average drill accuracy.

### `POST /api/practice`
Records a newly verified practice session.

**Request Body:**
```json
{
  "signsRecognized": 1,
  "durationSeconds": 15,
  "accuracy": 96.5
}
```

---

## 5. Streaming Audio TTS API (`/api/tts`)

### `GET /api/tts?text=<sentence>&lang=<languageCode>`
Generates or streams high-fidelity native Indian voice audio. If external cloud TTS is unconfigured, responds with `{ "fallback": "browser", "audio_url": null }` to prompt client-side `speechSynthesis`.
