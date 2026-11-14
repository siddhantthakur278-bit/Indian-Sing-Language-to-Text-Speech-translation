# Backend privacy and data handling

- The backend exposes text APIs only. Camera video, frames, landmarks, and raw
  biometric data must remain on the device and must not be sent to this service.
- API logs record operational metadata such as gloss count and language, not
  submitted gloss strings or credentials.
- When `LLM_API_KEY` is configured, non-emergency unmatched glosses may be
  submitted to Google's Gemini API for sentence enhancement. Emergency inputs
  bypass the provider. Operators should disclose this optional external
  processing and configure credentials only in server-side environment
  variables.
- Hindi and Marathi translation currently uses local committed CSV text. Missing
  translations fall back to the English sentence; no cloud translation call is
  made.
- Audio generation currently returns `audio_url: null`. Browser `speechSynthesis`
  is the speech path; no backend audio or video is stored.
- Rate-limit and response-cache state is in process memory and is cleared on
  restart. No persistence or analytics are implemented by the backend.
- The project is an assistive tool and is not a replacement for a qualified
  interpreter in legal, medical, or emergency settings. Emergency wording and
  classifications require ISL-domain-expert review.

Before any user study or collection of training videos, obtain informed consent
from each signer and follow the project's data collection and retention policy.
