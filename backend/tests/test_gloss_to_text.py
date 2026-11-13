"""
Unit Tests for Gloss-to-Sentence and Emergency Detection Engine
Compatible with both pytest and python's built-in unittest framework.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gloss_to_text import glosses_to_sentence, is_emergency_sequence, convert_glosses_with_rules


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
            (["YOU", "NAME", "WHAT"], "What is your name?"),
            (["ME", "NAME", "WHAT"], "What is my name?"),
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
            (["SPEAK", "SLOW", "PLEASE"], "Please speak slowly."),
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


if __name__ == "__main__":
    unittest.main()
