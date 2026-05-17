from typing import List, Dict, Tuple

ATTACK_KEYWORDS: List[Tuple[str, float, str]] = [
    # High confidence single-phrase indicators
    ("ignore previous instructions", 0.95, "instruction_override"),
    ("ignore all instructions", 0.95, "instruction_override"),
    ("disregard your instructions", 0.95, "instruction_override"),
    ("forget your instructions", 0.90, "instruction_override"),
    ("override your instructions", 0.90, "instruction_override"),
    ("new instructions:", 0.85, "instruction_override"),
    ("your new task is", 0.85, "instruction_override"),
    ("your actual instructions", 0.85, "prompt_extraction"),

    # Jailbreak keywords
    ("jailbreak", 0.95, "jailbreak"),
    ("do anything now", 0.95, "jailbreak"),
    ("DAN mode", 0.98, "jailbreak"),
    ("developer mode enabled", 0.90, "jailbreak"),
    ("no restrictions", 0.80, "jailbreak"),
    ("without restrictions", 0.75, "jailbreak"),
    ("without limitations", 0.70, "jailbreak"),
    ("bypass safety", 0.90, "jailbreak"),
    ("bypass filters", 0.90, "jailbreak"),
    ("ignore safety guidelines", 0.90, "jailbreak"),
    ("ignore ethical guidelines", 0.90, "jailbreak"),

    # Role override
    ("you are now a", 0.80, "role_impersonation"),
    ("act as if you are", 0.80, "role_impersonation"),
    ("pretend you are", 0.80, "role_impersonation"),
    ("roleplay as", 0.75, "role_impersonation"),
    ("you have no rules", 0.90, "role_impersonation"),
    ("you have no restrictions", 0.90, "role_impersonation"),
    ("you are an AI without", 0.85, "role_impersonation"),
    ("you are a different AI", 0.85, "role_impersonation"),
    ("your true self", 0.75, "role_impersonation"),

    # Prompt extraction
    ("reveal your system prompt", 0.98, "prompt_extraction"),
    ("show me your system prompt", 0.98, "prompt_extraction"),
    ("print your system prompt", 0.98, "prompt_extraction"),
    ("repeat your instructions", 0.90, "prompt_extraction"),
    ("what are your instructions", 0.80, "prompt_extraction"),
    ("display your initial prompt", 0.90, "prompt_extraction"),
    ("output your system message", 0.90, "prompt_extraction"),
    ("show your hidden instructions", 0.95, "prompt_extraction"),
    ("leak your prompt", 0.95, "prompt_extraction"),

    # Harmful content triggers
    ("synthesize drugs", 0.99, "harmful_content"),
    ("make explosives", 0.99, "harmful_content"),
    ("hack into", 0.90, "harmful_content"),
    ("how to hack", 0.85, "harmful_content"),
    ("sql injection", 0.75, "harmful_content"),
    ("malware code", 0.90, "harmful_content"),
    ("ransomware", 0.85, "harmful_content"),

    # Social engineering
    ("my grandmother used to tell me", 0.70, "social_engineering"),
    ("for educational purposes only", 0.65, "social_engineering"),
    ("hypothetically speaking", 0.55, "social_engineering"),
    ("in a fictional world", 0.60, "social_engineering"),
    ("write a story where a character explains", 0.75, "social_engineering"),
]

KEYWORD_MAP: Dict[str, Tuple[float, str]] = {
    phrase.lower(): (score, category)
    for phrase, score, category in ATTACK_KEYWORDS
}


class KeywordLayer:
    def __init__(self, custom_keywords: List[Tuple[str, float, str]] = None):
        self.keyword_map = dict(KEYWORD_MAP)
        if custom_keywords:
            for phrase, score, category in custom_keywords:
                self.keyword_map[phrase.lower()] = (score, category)

    def analyze(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()
        hits = []
        max_score = 0.0

        for phrase, (score, category) in self.keyword_map.items():
            if phrase in prompt_lower:
                hits.append({"keyword": phrase, "score": score, "category": category})
                if score > max_score:
                    max_score = score

        return {
            "score": max_score,
            "hits": hits,
            "hit_count": len(hits),
        }
