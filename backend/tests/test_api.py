"""
API Integration and Endpoint Contract Tests
===========================================
Tests Contract 7.2 from AGENTS.md:
- GET /health -> {"status": "ok"}
- POST /api/sentence -> sentence, translated, emergency, audio_url
- Validation: invalid lang codes and empty gloss lists rejected with 422
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    client = None


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        if not HAS_FASTAPI:
            self.skipTest("FastAPI TestClient not available in current environment")

    def test_health_check_endpoint(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_sentence_translation_endpoint_success(self):
        payload = {
            "glosses": ["ME", "HOSPITAL", "GO"],
            "lang": "hi"
        }
        response = client.post("/api/sentence", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sentence", data)
        self.assertIn("translated", data)
        self.assertEqual(data["lang"], "hi")
        self.assertTrue(data["emergency"] is True or "hospital" in data["sentence"].lower())
        self.assertIsNone(data["audio_url"])

    def test_sentence_translation_emergency_response(self):
        payload = {
            "glosses": ["HELP", "PAIN"],
            "lang": "mr"
        }
        response = client.post("/api/sentence", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["emergency"])
        self.assertEqual(data["lang"], "mr")

    def test_invalid_language_code(self):
        payload = {
            "glosses": ["HELLO"],
            "lang": "invalid_lang_code"
        }
        response = client.post("/api/sentence", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_empty_glosses(self):
        payload = {
            "glosses": [],
            "lang": "en"
        }
        response = client.post("/api/sentence", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
