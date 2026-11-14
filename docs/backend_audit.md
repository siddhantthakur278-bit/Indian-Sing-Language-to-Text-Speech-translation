# Backend implementation status

This status describes repository implementation, not production readiness.

## NLP and API

- `backend/gloss_to_text.py` provides deterministic templates, emergency
  handling, ordinary heuristics, optional Gemini enhancement, and safe fallback.
- Exact emergency templates and emergency keyword handling run before ordinary
  rules. Emergency sequences bypass Gemini.
- The Gemini adapter is optional, uses `LLM_API_KEY` and `LLM_MODEL`, and falls
  back locally on provider errors or invalid output.
- `POST /api/sentence` validates each normalized gloss against
  `data/classes.json`, rejects `IDLE`, and returns HTTP 400 for vocabulary errors.
- `POST /api/text-to-gloss` is a bounded rule-based English word mapper, not a
  general-purpose or domain-verified ISL translator.
- Both POST endpoints share the configured per-client in-memory rate limit.
- Sentence responses are held in a bounded in-memory cache.

## Translation and TTS

- Hindi and Marathi use exact offline entries in `data/gloss_pairs.csv`.
- Missing offline translations return the English source unchanged.
- Translation cache storage is bounded and thread-safe.
- Bhashini and cloud TTS are not implemented. TTS returns `audio_url: null` for
  browser `speechSynthesis` fallback.

## Gloss dataset

The original CSV had 219 rows. Sixty-nine rows contained glosses absent from the
official 70-class vocabulary and were excluded rather than rewritten with
unverified substitutions. One identical duplicate record was also removed. The
current file has 149 rows; all retained glosses
are canonical and all Hindi/Marathi fields are nonempty Devanagari text. This
checks field shape and script, not translation quality. Coverage is 67 of 69
non-`IDLE` classes; `HEAR` and `SEE` do not yet have dataset rows. No
translations were generated to fill the gap.

Emergency labels are explicit boolean values. Twelve rows differ from a simple
“contains one of HELP/PAIN/POLICE/AMBULANCE/FIRE/ACCIDENT/EMERGENCY/DANGER”
indicator. This heuristic is not an authoritative emergency policy; neither
labels nor emergency wording should be changed without ISL-domain-expert review.
The sequence `DOCTOR CALL PLEASE` has both `true` and `false` labels; this
conflict is retained and flagged for domain review rather than silently resolved.

## Verification boundaries

Automated tests cover input validation, offline lookup, provider mocks, cache and
limiter behavior, and emergency bypass. They do not validate translation
quality, ISL grammar, real-user usability, or emergency semantics. These require
review by fluent ISL users/interpreters and user testing.

See [backend test report](./BACKEND_TEST_REPORT.md), [API reference](./API.md),
[configuration](./BACKEND_CONFIGURATION.md), and [privacy notes](./PRIVACY.md).
