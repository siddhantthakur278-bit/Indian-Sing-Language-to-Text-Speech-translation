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

import re
import logging
from typing import List, Tuple, Optional

from backend.llm import generate_text

logger = logging.getLogger(__name__)

LLM_PROMPT_TEMPLATE = """You convert Indian Sign Language gloss sequences into one natural, polite English sentence.
ISL word order is often Subject-Object-Verb; reorder and add small function words
(is, the, to, a) as needed. Do not add new facts. Output only the sentence.

Glosses: ME MARKET GO        -> I am going to the market.
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
    # Classification and urgency wording require ISL-domain-expert approval.
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
    ("PLEASE", "WAIT"): "Please wait a moment.",
    ("STOP", "PLEASE"): "Please stop here.",
    ("WRITE", "PLEASE"): "Please write it down.",
    ("WHEN", "COME"): "When will you come?",
    ("WHY", "GO"): "Why are you going?",
    ("HOW", "GO"): "How do I get there?",
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

    upper_glosses = [g.upper() for g in glosses]

    # Emergency keywords take priority over every ordinary rule and heuristic.
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

    # Ordinary exact templates run only after emergency classification.
    if tuple_key in RULE_TEMPLATES:
        return RULE_TEMPLATES[tuple_key], False

    # Ordinary dynamic SOV heuristic matching
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
    """Use Gemini only for non-emergency glosses; leave failure to safe fallback."""
    prompt = LLM_PROMPT_TEMPLATE.format(glosses=gloss_str)
    return generate_text(prompt, source_glosses=gloss_str.split())


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



def sentence_to_glosses(text: str) -> List[str]:
    """
    Two-Way Mode Conversion: converts natural spoken sentence into an ISL gloss sequence.
    Applies English-to-ISL SOV grammar rules and matches against canonical vocabulary.
    """
    if not text or not text.strip():
        return []

    clean = re.sub(r'[^a-zA-Z0-9\s]', '', text).upper()
    words = clean.split()

    # Direct word mapping to ISL gloss tokens
    word_to_gloss = {
        "I": "ME",
        "ME": "ME",
        "MY": "ME",
        "YOU": "YOU",
        "YOUR": "YOU",
        "HE": "HE_SHE",
        "SHE": "HE_SHE",
        "WE": "WE",
        "US": "WE",
        "HOSPITAL": "HOSPITAL",
        "DOCTOR": "DOCTOR",
        "POLICE": "POLICE",
        "AMBULANCE": "AMBULANCE",
        "WATER": "WATER",
        "FOOD": "FOOD",
        "EAT": "EAT",
        "DRINK": "DRINK",
        "GO": "GO",
        "GOING": "GO",
        "COME": "COME",
        "COMING": "COME",
        "HELP": "HELP",
        "PAIN": "PAIN",
        "FIRE": "FIRE",
        "HELLO": "HELLO",
        "HI": "HELLO",
        "THANKS": "THANK_YOU",
        "THANK": "THANK_YOU",
        "SORRY": "SORRY",
        "PLEASE": "PLEASE",
        "WELCOME": "WELCOME",
        "GOODBYE": "GOODBYE",
        "BYE": "GOODBYE",
        "SCHOOL": "SCHOOL",
        "MARKET": "MARKET",
        "HOME": "HOME",
        "WORK": "WORK",
        "SLEEP": "SLEEP",
        "WHAT": "WHAT",
        "WHERE": "WHERE",
        "WHEN": "WHEN",
        "WHO": "WHO",
        "WHY": "WHY",
        "HOW": "HOW",
        "WANT": "WANT",
        "NEED": "NEED",
        "UNDERSTAND": "UNDERSTAND",
        "STOP": "STOP",
        "WAIT": "WAIT",
    }

    gloss_tokens = []
    # Identify subject, object, and verb for SOV reordering if possible
    subjects = []
    objects = []
    verbs = []
    questions = []

    for w in words:
        gloss = word_to_gloss.get(w)
        if not gloss:
            continue
        if gloss in {"ME", "YOU", "HE_SHE", "WE"}:
            subjects.append(gloss)
        elif gloss in {"GO", "COME", "EAT", "DRINK", "STOP", "WAIT"}:
            verbs.append(gloss)
        elif gloss in {"WHAT", "WHERE", "WHEN", "WHO", "WHY", "HOW"}:
            questions.append(gloss)
        else:
            objects.append(gloss)

    # In ISL, word order is Subject -> Object -> Verb -> Question Marker
    reordered = subjects + objects + verbs + questions
    # Fallback to in-order extraction if no structured tokens identified
    if not reordered:
        for w in words:
            if w in word_to_gloss:
                reordered.append(word_to_gloss[w])

    # Deduplicate consecutive identical tokens
    final_glosses = []
    for g in reordered:
        if not final_glosses or final_glosses[-1] != g:
            final_glosses.append(g)

    return final_glosses
