"""
Unit Tests for Gloss-to-Sentence and Emergency Detection Engine
Compatible with both pytest and python's built-in unittest framework.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gloss_to_text import glosses_to_sentence, is_emergency_sequence, convert_glosses_with_rules, sentence_to_glosses
from vocabulary import VOCABULARY


class TestGlossToText(unittest.TestCase):

    def test_emergency_detection_flag(self):
        self.assertTrue(is_emergency_sequence(["HELP"]))
        self.assertTrue(is_emergency_sequence(["PAIN", "ME"]))
        self.assertTrue(is_emergency_sequence(["POLICE", "CALL"]))
        self.assertTrue(is_emergency_sequence(["FIRE"]))
        self.assertFalse(is_emergency_sequence(["HELLO", "FRIEND"]))

    def test_emergency_templates_bypass_llm(self):
        sent, is_em = glosses_to_sentence(["HELP"])
        self.assertTrue(is_em)
        self.assertEqual(sent, "Please help me.")

        sent, is_em = glosses_to_sentence(["HELP", "ME", "HOSPITAL"])
        self.assertTrue(is_em)
        self.assertIn("hospital", sent.lower())

        sent, is_em = glosses_to_sentence(["POLICE", "CALL", "PLEASE"])
        self.assertTrue(is_em)
        self.assertIn("police", sent.lower())

    def test_greetings_and_basic_rules(self):
        cases = [
            (["HELLO"], "Hello!"),
            (["HELLO", "HOW", "YOU"], "Hello, how are you?"),
            (["THANK_YOU"], "Thank you very much."),
            (["SORRY"], "I am sorry."),
            (["WELCOME"], "You are welcome."),
            (["GOODBYE"], "Goodbye, take care."),
            (["ME", "MARKET", "GO"], "I am going to the market."),
            (["ME", "HOME", "GO"], "I am going home."),
            (["ME", "SCHOOL", "GO"], "I am going to school."),
            (["ME", "WORK", "GO"], "I am going to work."),
            (["FOOD", "WANT"], "I want food."),
            (["WATER", "PLEASE"], "Could I please have some water?"),
            (["TOILET", "WHERE"], "Where is the washroom?"),
            (["TIME", "WHAT"], "What time is it?"),
            (["ME", "UNDERSTAND"], "I understand."),
            (["PLEASE", "WAIT"], "Please wait a moment."),
            (["STOP", "PLEASE"], "Please stop here."),
            (["WRITE", "PLEASE"], "Please write it down."),
        ]
        for glosses, expected in cases:
            sent, is_em = glosses_to_sentence(glosses)
            self.assertEqual(sent, expected)
            self.assertFalse(is_em)

    def test_empty_and_whitespace_glosses(self):
        sent, is_em = glosses_to_sentence([])
        self.assertEqual(sent, "")
        self.assertFalse(is_em)

        sent, is_em = glosses_to_sentence(["   ", ""])
        self.assertEqual(sent, "")
        self.assertFalse(is_em)

    def test_dynamic_sov_places(self):
        sent, is_em = glosses_to_sentence(["ME", "BANK", "GO"])
        self.assertEqual(sent, "I am going to the Bank.")
        self.assertFalse(is_em)

    def test_fallback_graceful_join(self):
        sent, is_em = glosses_to_sentence(["BOOK", "READ"])
        self.assertEqual(sent, "Book read.")
        self.assertFalse(is_em)

    def test_sentence_to_glosses_two_way_mode(self):
        # Spoken input: "I am going to the hospital"
        glosses = sentence_to_glosses("I am going to the hospital")
        self.assertIn("ME", glosses)
        self.assertIn("HOSPITAL", glosses)
        self.assertIn("GO", glosses)

        # Spoken input: "Where is the doctor?"
        glosses = sentence_to_glosses("Where is the doctor")
        self.assertIn("DOCTOR", glosses)
        self.assertIn("WHERE", glosses)

        # Empty string
        self.assertEqual(sentence_to_glosses(""), [])

    def test_all_rule_and_emergency_template_tokens_are_official(self):
        import gloss_to_text

        for templates in (
            gloss_to_text.RULE_TEMPLATES,
            gloss_to_text.EMERGENCY_TEMPLATES,
        ):
            for gloss_sequence in templates:
                self.assertTrue(
                    set(gloss_sequence).issubset(VOCABULARY),
                    f"Unsupported template tokens in {gloss_sequence}",
                )

        self.assertNotIn(("YOU", "HELP", "ME", "CAN"), gloss_to_text.RULE_TEMPLATES)
        self.assertNotIn(("WHAT", "HAPPEN"), gloss_to_text.RULE_TEMPLATES)
        self.assertNotIn(("FAMILY", "WHERE"), gloss_to_text.RULE_TEMPLATES)
        self.assertNotIn(("ME", "HUNGRY"), gloss_to_text.RULE_TEMPLATES)
        self.assertNotIn(("ME", "THIRSTY"), gloss_to_text.RULE_TEMPLATES)

    def test_doctor_need_emergency_template_is_preserved_pending_expert_review(self):
        import gloss_to_text

        # Classification and urgency wording are not ISL-domain-expert approved.
        self.assertEqual(
            gloss_to_text.EMERGENCY_TEMPLATES[("ME", "DOCTOR", "NEED")],
            "I need to see a doctor urgently.",
        )
        self.assertEqual(
            glosses_to_sentence(["ME", "DOCTOR", "NEED"]),
            ("I need to see a doctor urgently.", True),
        )


if __name__ == "__main__":
    unittest.main()
