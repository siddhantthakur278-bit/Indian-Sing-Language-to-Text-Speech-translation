"""
Safety-Critical Emergency Guardrail Tests
Validates that emergency expressions ALWAYS return emergency=True and never hallucinate.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gloss_to_text import glosses_to_sentence, is_emergency_sequence


class TestEmergencyGuardrails(unittest.TestCase):

    def test_all_emergency_keywords_flagged(self):
        critical_keywords = ["HELP", "PAIN", "POLICE", "AMBULANCE", "FIRE", "ACCIDENT", "EMERGENCY", "DANGER"]
        for kw in critical_keywords:
            self.assertTrue(is_emergency_sequence([kw]), f"Keyword {kw} failed to trigger emergency flag")
            self.assertTrue(is_emergency_sequence(["PLEASE", kw]), f"Compound phrase with {kw} failed")

    def test_emergency_fixed_templates_invariant(self):
        # HELP
        s, is_em = glosses_to_sentence(["HELP"])
        self.assertTrue(is_em)
        self.assertEqual(s, "Please help me.")

        # PAIN
        s, is_em = glosses_to_sentence(["PAIN"])
        self.assertTrue(is_em)
        self.assertIn("pain", s.lower())

        # POLICE
        s, is_em = glosses_to_sentence(["POLICE", "CALL", "PLEASE"])
        self.assertTrue(is_em)
        self.assertIn("police", s.lower())

        # AMBULANCE
        s, is_em = glosses_to_sentence(["AMBULANCE", "CALL", "PLEASE"])
        self.assertTrue(is_em)
        self.assertIn("ambulance", s.lower())

    def test_non_emergency_never_falsely_flagged(self):
        safe_phrases = [
            ["HELLO"],
            ["THANK_YOU"],
            ["ME", "MARKET", "GO"],
            ["FOOD", "WANT"],
            ["WATER", "PLEASE"],
            ["WHAT", "TIME", "MEET"],
            ["YOU", "NAME", "WHAT"],
        ]
        for phrase in safe_phrases:
            s, is_em = glosses_to_sentence(phrase)
            self.assertFalse(is_em, f"Safe phrase {phrase} falsely flagged as emergency")


if __name__ == "__main__":
    unittest.main()
