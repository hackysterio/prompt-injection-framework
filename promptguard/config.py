from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GuardConfig:
    heuristic_weight: float = 0.40
    keyword_weight: float = 0.30
    similarity_weight: float = 0.30

    safe_threshold: float = 0.30
    warn_threshold: float = 0.55
    block_threshold: float = 0.75

    enable_heuristic: bool = True
    enable_keyword: bool = True
    enable_similarity: bool = True

    log_to_file: bool = True
    log_file_path: str = "promptguard.log"
    log_level: str = "INFO"

    similarity_top_k: int = 5
    custom_attack_phrases: list = field(default_factory=list)
    fallback_response: str = (
        "I'm sorry, I cannot process that request. "
        "Please rephrase your message."
    )

    def validate(self) -> None:
        total = (
            (self.heuristic_weight if self.enable_heuristic else 0)
            + (self.keyword_weight if self.enable_keyword else 0)
            + (self.similarity_weight if self.enable_similarity else 0)
        )
        if total == 0:
            raise ValueError("At least one detection layer must be enabled.")
        if not (0 < self.safe_threshold < self.warn_threshold < self.block_threshold <= 1.0):
            raise ValueError("Thresholds must satisfy: 0 < safe < warn < block <= 1.0")
