# Backend Implementation Audit

**Owner:** Abhi – NLP, Speech and Backend

## 1. Gloss-to-Sentence
File: backend/gloss_to_text.py

- Rule-based sentence templates exist.
- Emergency phrase detection exists.
- LLM API integration is incomplete.
- General sentence patterns need improvement.

## 2. FastAPI Backend
File: backend/main.py

- GET /health exists.
- POST /api/sentence exists.
- Request and response models exist.
- Language validation exists.
- Maximum gloss count is limited.
- Vocabulary validation needs implementation.
- Rate limiting needs implementation.
- Feature availability is not reported by health endpoint.

## 3. Translation
File: backend/translate.py

- Translation function exists.
- In-memory translation cache exists.
- Bhashini provider integration is incomplete.
- Missing translations currently fall back to English.

## 4. Text-to-Speech
File: backend/tts.py

- Indian language locale mapping exists.
- Browser speech synthesis is used by the frontend.
- Cloud TTS integration is incomplete.

## 5. Dataset
Files:
- data/classes.json
- data/gloss_pairs.csv

- Vocabulary contains 70 classes.
- Gloss-sentence examples exist.
- Dataset quality and translation coverage require verification.

## 6. Testing

Existing tests:
- backend/tests/test_api.py
- backend/tests/test_gloss_to_text.py

Additional testing is required for vocabulary validation,
translation fallbacks, emergency handling and rate limiting.

## 7. Development Roadmap

1. Backend configuration and schemas.
2. Vocabulary validation.
3. NLP improvements.
4. Emergency phrase separation.
5. LLM integration.
6. Translation adapters and caching.
7. TTS improvements.
8. API security and validation.
9. Automated testing.
10. Deployment and documentation.

## 8. Development Principles

- Never commit API secrets.
- Never send signing videos to the backend.
- Never present mock integrations as real integrations.
- Preserve the agreed frontend API contract.
- Test every meaningful implementation.
