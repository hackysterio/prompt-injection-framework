import re
from typing import List, Tuple

HEURISTIC_PATTERNS: List[Tuple[str, float, str]] = [
    # Instruction override attacks
    (r"\bignore\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|directives?|guidelines?|rules?|prompts?)\b", 0.95, "instruction_override"),
    (r"\bdisregard\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|rules?|guidelines?)\b", 0.95, "instruction_override"),
    (r"\bforget\s+(all\s+)?(previous|prior|above|your|everything)\s*(instructions?|rules?|guidelines?|you.ve been told)?\b", 0.90, "instruction_override"),
    (r"\boverride\s+(your\s+)?(system\s+)?(prompt|instructions?|guidelines?|programming)\b", 0.90, "instruction_override"),
    (r"\bdo\s+not\s+follow\s+(your\s+)?(previous|prior|system)?\s*(instructions?|guidelines?|rules?)\b", 0.90, "instruction_override"),
    (r"\byour\s+(new|real|true|actual|updated)\s+(instructions?|task|role|purpose|directive)\b", 0.85, "instruction_override"),
    (r"\bfrom\s+(now|this point)\s+on\b.{0,50}(ignore|forget|disregard)", 0.85, "instruction_override"),

    # Role impersonation attacks
    (r"\byou\s+are\s+now\s+(a|an|the)\b", 0.80, "role_impersonation"),
    (r"\bpretend\s+(you\s+are|to\s+be)\b", 0.80, "role_impersonation"),
    (r"\bact\s+as\s+(a|an|the|if\s+you\s+are)\b", 0.75, "role_impersonation"),
    (r"\bimagine\s+you\s+are\s+(a|an|the)\b", 0.70, "role_impersonation"),
    (r"\bplay\s+(the\s+role|a\s+character)\s+of\b", 0.75, "role_impersonation"),
    (r"\bswitch\s+(to|into)\s+(a|an|the)?\s*(different|new|another)?\s*(mode|persona|role|character)\b", 0.80, "role_impersonation"),
    (r"\byou\s+have\s+no\s+(restrictions?|limits?|rules?|guidelines?)\b", 0.95, "role_impersonation"),

    # System prompt extraction
    (r"\b(reveal|show|print|display|tell me|output|repeat|write out|expose)\s+(your|the)?\s*(system\s+prompt|initial\s+prompt|original\s+instructions?|hidden\s+instructions?)\b", 0.95, "prompt_extraction"),
    (r"\bwhat\s+(are|were)\s+your\s+(original|initial|system|starting)\s+(instructions?|prompts?|guidelines?)\b", 0.90, "prompt_extraction"),
    (r"\brepeat\s+(everything|all)\s+(above|before|prior|previous)\b", 0.85, "prompt_extraction"),
    (r"\b(output|print|show)\s+.{0,20}(verbatim|word.for.word|exactly as)\b", 0.75, "prompt_extraction"),

    # Jailbreak triggers
    (r"\bDAN\b.{0,30}(mode|now|prompt|activated)", 0.98, "jailbreak"),
    (r"\bdo\s+anything\s+now\b", 0.95, "jailbreak"),
    (r"\bjailbreak\b", 0.95, "jailbreak"),
    (r"\bdeveloper\s+mode\b.{0,30}(enabled|activated|on)", 0.90, "jailbreak"),
    (r"\bunrestricted\s+mode\b", 0.90, "jailbreak"),
    (r"\bgod\s+mode\b", 0.85, "jailbreak"),
    (r"\bsuperuser\s+mode\b", 0.85, "jailbreak"),
    (r"\byou\s+are\s+(free|allowed|permitted|able)\s+(to|now)\s+(ignore|bypass|break|violate)\b", 0.90, "jailbreak"),

    # Delimiter/injection attacks
    (r"(</?(system|user|assistant|instruction|prompt|context)>)", 0.85, "delimiter_injection"),
    (r"(\[\[(SYS|INST|SYSTEM)\]\])", 0.90, "delimiter_injection"),
    (r"(###\s*(System|Instruction|Override|New Task))", 0.80, "delimiter_injection"),
    (r"(\[SYSTEM\]|\[INST\]|\[OVERRIDE\])", 0.85, "delimiter_injection"),

    # Obfuscation / encoding tricks
    (r"base64\s*:\s*[A-Za-z0-9+/]{20,}", 0.75, "obfuscation"),
    (r"(rot13|hex|unicode|encoded)\s*(instruction|message|command|prompt)", 0.80, "obfuscation"),

    # Data exfiltration
    (r"\b(send|transmit|exfiltrate|leak|email|forward)\s+.{0,30}(data|information|credentials?|passwords?|keys?|tokens?)\b", 0.85, "exfiltration"),
    (r"\b(steal|dump|extract)\s+.{0,20}(database|config|environment|secrets?)\b", 0.90, "exfiltration"),
    (r"\bprint\s+(all\s+)?(environment\s+variables?|api\s+keys?|secrets?)\b", 0.90, "exfiltration"),
]

COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE | re.DOTALL), score, category)
    for pattern, score, category in HEURISTIC_PATTERNS
]


class HeuristicLayer:
    def __init__(self, custom_patterns: List[Tuple[str, float, str]] = None):
        self.patterns = list(COMPILED_PATTERNS)
        if custom_patterns:
            for pattern, score, category in custom_patterns:
                self.patterns.append(
                    (re.compile(pattern, re.IGNORECASE | re.DOTALL), score, category)
                )

    def analyze(self, prompt: str) -> dict:
        matches = []
        max_score = 0.0

        for compiled, score, category in self.patterns:
            if compiled.search(prompt):
                matches.append({"pattern_category": category, "score": score})
                if score > max_score:
                    max_score = score

        return {
            "score": max_score,
            "matches": matches,
            "match_count": len(matches),
        }
