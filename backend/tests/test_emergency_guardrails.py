"""Regression tests for emergency sentence handling and guardrails."""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import gloss_to_text


class TestEmergencyGuardrails:
    def test_emergency_keywords_preceded_by_please_are_flagged(self):
        critical_keywords = [
            "HELP",
            "PAIN",
            "POLICE",
            "AMBULANCE",
            "FIRE",
            "ACCIDENT",
            "EMERGENCY",
            "DANGER",
        ]

        for keyword in critical_keywords:
            assert gloss_to_text.is_emergency_sequence(
                ["PLEASE", keyword]
            ), keyword

    def test_every_emergency_trigger_is_flagged_end_to_end(self):
        critical_keywords = [
            "HELP",
            "PAIN",
            "POLICE",
            "AMBULANCE",
            "FIRE",
            "ACCIDENT",
            "EMERGENCY",
            "DANGER",
        ]

        with patch.object(gloss_to_text, "query_llm_for_sentence") as llm:
            for keyword in critical_keywords:
                sentence, is_emergency = gloss_to_text.glosses_to_sentence(
                    [keyword]
                )

                assert sentence
                assert is_emergency is True, keyword

        llm.assert_not_called()

    def test_every_exact_emergency_template_is_returned_unchanged(self):
        with patch.object(gloss_to_text, "query_llm_for_sentence") as llm:
            for gloss_sequence, expected_sentence in (
                gloss_to_text.EMERGENCY_TEMPLATES.items()
            ):
                sentence, is_emergency = gloss_to_text.glosses_to_sentence(
                    list(gloss_sequence)
                )

                assert is_emergency is True, gloss_sequence
                assert sentence == expected_sentence, gloss_sequence

        llm.assert_not_called()

    def test_emergency_sequences_bypass_llm_and_return_immediately(self):
        emergency_sequences = [
            ["HELP"],
            ["PAIN", "NEED"],
            ["POLICE", "CALL", "PLEASE"],
            ["FIRE", "WHERE"],
        ]

        with patch.object(
            gloss_to_text,
            "query_llm_for_sentence",
            side_effect=AssertionError("Emergency input must bypass the LLM"),
        ) as llm:
            for glosses in emergency_sequences:
                sentence, is_emergency = gloss_to_text.glosses_to_sentence(glosses)

                assert sentence
                assert is_emergency is True, glosses

        llm.assert_not_called()

    def test_mixed_sequences_with_each_emergency_trigger_bypass_llm(self):
        critical_keywords = [
            "HELP",
            "PAIN",
            "POLICE",
            "AMBULANCE",
            "FIRE",
            "ACCIDENT",
            "EMERGENCY",
            "DANGER",
        ]

        with patch.object(
            gloss_to_text,
            "query_llm_for_sentence",
            side_effect=AssertionError("Emergency input must bypass the LLM"),
        ) as llm:
            for keyword in critical_keywords:
                sequence = ["ME", keyword, "WANT"]
                sentence, is_emergency = gloss_to_text.glosses_to_sentence(
                    sequence
                )

                assert sentence
                assert is_emergency is True, sequence

        llm.assert_not_called()

    def test_you_help_me_can_is_emergency_in_direct_nlp_engine(self):
        with patch.object(
            gloss_to_text,
            "query_llm_for_sentence",
            side_effect=AssertionError("Emergency input must bypass the LLM"),
        ) as llm:
            sentence, is_emergency = gloss_to_text.glosses_to_sentence(
                ["YOU", "HELP", "ME", "CAN"]
            )

        assert sentence == "Emergency! Please help me immediately."
        assert is_emergency is True
        llm.assert_not_called()

    def test_emergency_detection_precedes_conflicting_ordinary_exact_template(
        self,
    ):
        sequence = ("YOU", "HELP", "ME", "CAN")
        conflicting_ordinary_text = "Ordinary template must not win."

        with (
            patch.dict(
                gloss_to_text.RULE_TEMPLATES,
                {sequence: conflicting_ordinary_text},
            ),
            patch.object(
                gloss_to_text,
                "query_llm_for_sentence",
                side_effect=AssertionError("Emergency input must bypass the LLM"),
            ) as llm,
        ):
            sentence, is_emergency = gloss_to_text.glosses_to_sentence(
                list(sequence)
            )

        assert sentence == "Emergency! Please help me immediately."
        assert sentence != conflicting_ordinary_text
        assert is_emergency is True
        llm.assert_not_called()

    def test_ordinary_unmatched_sequence_uses_safe_fallback(self):
        glosses = ["MEET", "FRIEND", "TOMORROW"]

        with patch.object(
            gloss_to_text, "query_llm_for_sentence", return_value=None
        ) as llm:
            sentence, is_emergency = gloss_to_text.glosses_to_sentence(glosses)

        assert sentence == "Meet friend tomorrow."
        assert is_emergency is False
        llm.assert_called_once_with("MEET FRIEND TOMORROW")

    def test_emergency_priority_over_ordinary_dynamic_heuristics(self):
        cases = [
            (["HELP", "WANT"], "Emergency! Please help me immediately."),
            (["PAIN", "NEED"], "I am in severe pain, please help."),
            (["DANGER", "WHERE"], "Emergency! Please help me immediately."),
        ]

        with patch.object(
            gloss_to_text,
            "query_llm_for_sentence",
            side_effect=AssertionError("Emergency input must bypass the LLM"),
        ) as llm:
            for glosses, expected_sentence in cases:
                sentence, is_emergency = gloss_to_text.glosses_to_sentence(glosses)

                assert is_emergency is True, glosses
                assert sentence == expected_sentence, glosses

        llm.assert_not_called()

    def test_safe_non_emergency_phrases_remain_unflagged(self):
        safe_phrases = [
            ["HELLO"],
            ["THANK_YOU"],
            ["ME", "MARKET", "GO"],
            ["FOOD", "WANT"],
            ["WATER", "PLEASE"],
            ["WHAT", "TIME", "MEET"],
            ["ME", "HOME", "GO"],
            ["ME", "UNDERSTAND"],
            ["PLEASE", "WAIT"],
        ]

        with patch.object(gloss_to_text, "query_llm_for_sentence", return_value=None):
            for phrase in safe_phrases:
                sentence, is_emergency = gloss_to_text.glosses_to_sentence(phrase)

                assert sentence
                assert is_emergency is False, phrase

    def test_single_gloss_incomplete_sequences_keep_current_classification(self):
        expected = {
            "HELP": ("Please help me.", True),
            "PAIN": ("I am in severe pain.", True),
            "DOCTOR": ("Doctor.", False),
            "HOSPITAL": ("Hospital.", False),
            "MEDICINE": ("Medicine.", False),
            "CALL": ("Call.", False),
        }

        with patch.object(gloss_to_text, "query_llm_for_sentence", return_value=None):
            for gloss, expected_result in expected.items():
                assert gloss_to_text.glosses_to_sentence([gloss]) == expected_result


if __name__ == "__main__":
    import unittest

    unittest.main()
