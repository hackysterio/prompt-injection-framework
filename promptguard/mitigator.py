import re
from enum import Enum
from typing import Optional


class MitigationAction(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    SANITIZE = "SANITIZE"
    BLOCK = "BLOCK"


_SANITIZE_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above|earlier|your)\s+(instructions?|directives?|guidelines?|rules?|prompts?)\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|rules?|guidelines?)\b", re.IGNORECASE),
    re.compile(r"\bforget\s+(all\s+)?(previous|prior|above|your|everything)\s*(instructions?|rules?|guidelines?)?\b", re.IGNORECASE),
    re.compile(r"\boverride\s+(your\s+)?(system\s+)?(prompt|instructions?|guidelines?|programming)\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(a|an|the|if\s+you\s+are)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(a|an|the)\b", re.IGNORECASE),
    re.compile(r"(</?(system|user|assistant|instruction|prompt|context)>)", re.IGNORECASE),
    re.compile(r"(\[\[(SYS|INST|SYSTEM)\]\])", re.IGNORECASE),
    re.compile(r"(###\s*(System|Instruction|Override|New Task))", re.IGNORECASE),
]

_PLACEHOLDER = "[REMOVED]"


class Mitigator:
    def __init__(self, fallback_response: str):
        self.fallback_response = fallback_response

    def decide_action(self, risk_score: float, config) -> MitigationAction:
        if risk_score < config.safe_threshold:
            return MitigationAction.ALLOW
        elif risk_score < config.warn_threshold:
            return MitigationAction.WARN
        elif risk_score < config.block_threshold:
            return MitigationAction.SANITIZE
        else:
            return MitigationAction.BLOCK

    def sanitize(self, prompt: str) -> str:
        sanitized = prompt
        for pattern in _SANITIZE_PATTERNS:
            sanitized = pattern.sub(_PLACEHOLDER, sanitized)
        sanitized = " ".join(sanitized.split())
        return sanitized

    def apply(self, prompt: str, action: MitigationAction) -> dict:
        if action == MitigationAction.ALLOW:
            return {
                "action": action,
                "safe_to_process": True,
                "output_prompt": prompt,
                "response_override": None,
            }
        elif action == MitigationAction.WARN:
            return {
                "action": action,
                "safe_to_process": True,
                "output_prompt": prompt,
                "response_override": None,
            }
        elif action == MitigationAction.SANITIZE:
            return {
                "action": action,
                "safe_to_process": True,
                "output_prompt": self.sanitize(prompt),
                "response_override": None,
            }
        else:
            return {
                "action": action,
                "safe_to_process": False,
                "output_prompt": None,
                "response_override": self.fallback_response,
            }
