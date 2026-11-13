"""
ISL Gloss-to-Sentence Natural Language Processing Engine
========================================================
Translates ISL gloss sequences (typically Subject-Object-Verb) into grammatically
natural English sentences using:
1. Fast rule-based dictionary templates for instant, offline conversion.
2. Hard-coded safety-critical emergency phrase detection (bypasses LLM).
3. Question and polite request transformation heuristics.
4. Optional LLM few-shot prompt enhancement when LLM_API_KEY is configured.
"""

import os
import re
import json
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

LLM_PROMPT_TEMPLATE = """You convert Indian Sign Language gloss sequences into one natural, polite English sentence.
ISL word order is often Subject-Object-Verb; reorder and add small function words
(is, the, to, a) as needed. Do not add new facts. Output only the sentence.

Glosses: ME MARKET GO        -> I am going to the market.
Glosses: YOU NAME WHAT       -> What is your name?
Glosses: HELP ME HOSPITAL    -> Please help me, I need to go to the hospital.
Glosses: {glosses}           -> """

# Fixed verified emergency dictionary (Safety Rule: Never let an LLM rewrite emergency phrases)
EMERGENCY_TEMPLATES = {
    ("HELP",): "Please help me.",
    ("HELP", "ME"): "Please help me immediately.",
    ("PAIN",): "I am in severe pain.",
    ("ME", "PAIN"): "I am in pain and need assistance.",
    ("HELP", "ME", "PAIN"): "Please help me, I am in severe pain.",
    ("HOSPITAL", "GO", "NEED"): "I need to go to the hospital immediately.",
    ("ME", "HOSPITAL", "GO"): "I need to go to the hospital.",
    ("HELP", "ME", "HOSPITAL"): "Please help me, I need to go to the hospital.",
    ("DOCTOR", "CALL", "PLEASE"): "Please call a doctor immediately.",
    ("DOCTOR", "NEED"): "I need a doctor urgently.",
    ("ME", "DOCTOR", "NEED"): "I need to see a doctor urgently.",
    ("AMBULANCE", "CALL", "PLEASE"): "Please call an ambulance right away.",
    ("POLICE", "CALL", "PLEASE"): "Please call the police immediately.",
    ("POLICE", "NEED"): "I need police assistance.",
    ("FIRE", "HELP"): "Fire! Please send emergency help!",
    ("FIRE", "CALL", "POLICE"): "There is a fire, please call emergency services.",
    ("ACCIDENT", "HELP"): "There has been an accident, please help.",
    ("ACCIDENT", "AMBULANCE", "CALL"): "An accident occurred, please call an ambulance.",
    ("DANGER", "STOP"): "Danger ahead, please stop!",
    ("EMERGENCY", "HELP", "ME"): "Emergency! Please help me!",
}

# General Rule-Based Templates
RULE_TEMPLATES = {
    ("HELLO",): "Hello!",
    ("HELLO", "HOW", "YOU"): "Hello, how are you?",
    ("THANK_YOU",): "Thank you very much.",
    ("SORRY",): "I am sorry.",
    ("PLEASE",): "Please.",
    ("WELCOME",): "You are welcome.",
    ("GOODBYE",): "Goodbye, take care.",
    ("ME", "NAME", "WHAT"): "What is my name?",
    ("YOU", "NAME", "WHAT"): "What is your name?",
    ("ME", "MARKET", "GO"): "I am going to the market.",
    ("ME", "HOME", "GO"): "I am going home.",
    ("ME", "SCHOOL", "GO"): "I am going to school.",
    ("ME", "WORK", "GO"): "I am going to work.",
    ("FOOD", "WANT"): "I want food.",
    ("ME", "FOOD", "EAT", "WANT"): "I want to eat food.",
    ("WATER", "DRINK", "WANT"): "I want to drink water.",
    ("WATER", "PLEASE"): "Could I please have some water?",
    ("TOILET", "WHERE"): "Where is the washroom?",
    ("TIME", "WHAT"): "What time is it?",
    ("ME", "UNDERSTAND"): "I understand.",
    ("ME", "NOT", "UNDERSTAND"): "I do not understand.",
    ("PLEASE", "WAIT"): "Please wait a moment.",
    ("STOP", "PLEASE"): "Please stop here.",
    ("WRITE", "PLEASE"): "Please write it down.",
    ("SPEAK", "SLOW", "PLEASE"): "Please speak slowly.",
    ("YOU", "HELP", "ME", "CAN"): "Can you please help me?",
    ("WHEN", "COME"): "When will you come?",
    ("WHY", "GO"): "Why are you going?",
    ("HOW", "GO"): "How do I get there?",
    ("WHAT", "HAPPEN"): "What happened?",
    ("FAMILY", "WHERE"): "Where is my family?",
    ("ME", "HUNGRY"): "I am hungry.",
    ("ME", "THIRSTY"): "I am thirsty.",
}


def is_emergency_sequence(glosses: List[str]) -> bool:
    """Checks whether the gloss list contains high-priority emergency triggers."""
    emergency_keywords = {"HELP", "PAIN", "POLICE", "AMBULANCE", "FIRE", "ACCIDENT", "EMERGENCY", "DANGER"}
    return any(g.upper() in emergency_keywords for g in glosses)


def convert_glosses_with_rules(glosses: List[str]) -> Tuple[Optional[str], bool]:
    """Attempts rule-based pattern matching on the gloss sequence."""
    tuple_key = tuple(g.upper() for g in glosses)

    # 1. Check exact emergency templates
    if tuple_key in EMERGENCY_TEMPLATES:
        return EMERGENCY_TEMPLATES[tuple_key], True

    # 2. Check general exact templates
    if tuple_key in RULE_TEMPLATES:
        return RULE_TEMPLATES[tuple_key], False

    # 3. Dynamic SOV heuristic matching
    upper_glosses = [g.upper() for g in glosses]

    # Check emergency heuristics
    if is_emergency_sequence(upper_glosses):
        if "HOSPITAL" in upper_glosses and "GO" in upper_glosses:
            return "Please help me, I need to get to the hospital immediately.", True
        if "DOCTOR" in upper_glosses:
            return "Please help me find a doctor.", True
        if "POLICE" in upper_glosses:
            return "Please call the police immediately.", True
        if "AMBULANCE" in upper_glosses:
            return "Please call an ambulance right away.", True
        if "PAIN" in upper_glosses:
            return "I am in severe pain, please help.", True
        return "Emergency! Please help me immediately.", True

    # Subject + Location + Verb heuristic (e.g. ME + X + GO)
    if len(upper_glosses) == 3 and upper_glosses[0] == "ME" and upper_glosses[2] == "GO":
        place = upper_glosses[1].capitalize()
        return f"I am going to the {place}.", False

    # Subject + Want / Need
    if "WANT" in upper_glosses or "NEED" in upper_glosses:
        items = [g.lower() for g in upper_glosses if g not in {"ME", "WANT", "NEED"}]
        verb = "need" if "NEED" in upper_glosses else "want"
        if items:
            return f"I {verb} {' '.join(items)}.", False

    # Question heuristics (X WHERE)
    if "WHERE" in upper_glosses:
        items = [g.lower() for g in upper_glosses if g != "WHERE"]
        if items:
            return f"Where is the {' '.join(items)}?", False

    return None, False


def query_llm_for_sentence(gloss_str: str) -> Optional[str]:
    """Calls external LLM if API key is configured."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return None

    try:
        import urllib.request
        model = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        # Placeholder for external HTTP invocation
        return None
    except Exception as e:
        logger.warning(f"LLM API query failed: {e}")
        return None


def glosses_to_sentence(glosses: List[str]) -> Tuple[str, bool]:
    """
    Main conversion entrypoint.
    Returns (natural_english_sentence, is_emergency_flag).
    """
    if not glosses:
        return "", False

    # Clean gloss tokens
    clean_glosses = [re.sub(r'[^A-Za-z0-9_]', '', g).upper() for g in glosses if g.strip()]
    if not clean_glosses:
        return "", False

    # 1. Rule & Emergency resolution
    rule_result, is_emergency = convert_glosses_with_rules(clean_glosses)
    if is_emergency or rule_result:
        return rule_result, is_emergency

    # 2. LLM Enhancement (non-emergency only)
    gloss_str = " ".join(clean_glosses)
    llm_result = query_llm_for_sentence(gloss_str)
    if llm_result:
        return llm_result.strip(), False

    # 3. Graceful fallback: join words into readable sentence
    fallback = " ".join(clean_glosses).capitalize() + "."
    return fallback, False
