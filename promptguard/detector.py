from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .config import GuardConfig
from .layers.heuristic import HeuristicLayer
from .layers.keyword import KeywordLayer
from .layers.similarity import SimilarityLayer
from .mitigator import MitigationAction, Mitigator
from .logger import get_logger


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _score_to_risk_level(score: float) -> RiskLevel:
    if score < 0.20:
        return RiskLevel.SAFE
    elif score < 0.40:
        return RiskLevel.LOW
    elif score < 0.60:
        return RiskLevel.MEDIUM
    elif score < 0.80:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


@dataclass
class DetectionResult:
    original_prompt: str
    risk_score: float
    risk_level: RiskLevel
    action: MitigationAction
    safe_to_process: bool
    output_prompt: Optional[str]
    response_override: Optional[str]
    layer_scores: Dict[str, float] = field(default_factory=dict)
    layer_details: Dict[str, Any] = field(default_factory=dict)
    threats_detected: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"PromptGuard Detection Result",
            f"  Risk Score   : {self.risk_score:.3f}",
            f"  Risk Level   : {self.risk_level.value}",
            f"  Action       : {self.action.value}",
            f"  Safe         : {self.safe_to_process}",
            f"  Threats      : {', '.join(self.threats_detected) if self.threats_detected else 'None'}",
        ]
        if self.response_override:
            lines.append(f"  Override Msg : {self.response_override}")
        return "\n".join(lines)


class PromptGuard:
    def __init__(self, config: Optional[GuardConfig] = None):
        self.config = config or GuardConfig()
        self.config.validate()

        log_file = self.config.log_file_path if self.config.log_to_file else None
        self._logger = get_logger("promptguard", log_file=log_file, level=self.config.log_level)

        self._heuristic = HeuristicLayer() if self.config.enable_heuristic else None
        self._keyword = KeywordLayer() if self.config.enable_keyword else None
        self._similarity = SimilarityLayer(top_k=self.config.similarity_top_k) if self.config.enable_similarity else None
        self._mitigator = Mitigator(fallback_response=self.config.fallback_response)

    def analyze(self, prompt: str) -> DetectionResult:
        if not prompt or not prompt.strip():
            return DetectionResult(
                original_prompt=prompt,
                risk_score=0.0,
                risk_level=RiskLevel.SAFE,
                action=MitigationAction.ALLOW,
                safe_to_process=True,
                output_prompt=prompt,
                response_override=None,
            )

        layer_scores: Dict[str, float] = {}
        layer_details: Dict[str, Any] = {}
        threats: List[str] = []
        active_weight_total = 0.0
        weighted_score = 0.0

        if self._heuristic:
            result = self._heuristic.analyze(prompt)
            layer_scores["heuristic"] = result["score"]
            layer_details["heuristic"] = result
            weighted_score += result["score"] * self.config.heuristic_weight
            active_weight_total += self.config.heuristic_weight
            for match in result["matches"]:
                cat = match["pattern_category"]
                if cat not in threats:
                    threats.append(cat)

        if self._keyword:
            result = self._keyword.analyze(prompt)
            layer_scores["keyword"] = result["score"]
            layer_details["keyword"] = result
            weighted_score += result["score"] * self.config.keyword_weight
            active_weight_total += self.config.keyword_weight
            for hit in result["hits"]:
                cat = hit["category"]
                if cat not in threats:
                    threats.append(cat)

        if self._similarity:
            result = self._similarity.analyze(prompt)
            layer_scores["similarity"] = result["score"]
            layer_details["similarity"] = result
            weighted_score += result["score"] * self.config.similarity_weight
            active_weight_total += self.config.similarity_weight

        if active_weight_total > 0:
            risk_score = weighted_score / active_weight_total
        else:
            risk_score = 0.0

        risk_score = round(min(max(risk_score, 0.0), 1.0), 4)
        risk_level = _score_to_risk_level(risk_score)
        action = self._mitigator.decide_action(risk_score, self.config)
        mitigation = self._mitigator.apply(prompt, action)

        result_obj = DetectionResult(
            original_prompt=prompt,
            risk_score=risk_score,
            risk_level=risk_level,
            action=action,
            safe_to_process=mitigation["safe_to_process"],
            output_prompt=mitigation["output_prompt"],
            response_override=mitigation["response_override"],
            layer_scores=layer_scores,
            layer_details=layer_details,
            threats_detected=threats,
        )

        self._log_result(result_obj)
        return result_obj

    def is_safe(self, prompt: str) -> bool:
        return self.analyze(prompt).safe_to_process

    def _log_result(self, result: DetectionResult) -> None:
        msg = (
            f"[{result.action.value}] score={result.risk_score:.3f} "
            f"level={result.risk_level.value} "
            f"threats={result.threats_detected} "
            f'prompt="{result.original_prompt[:80]}{"..." if len(result.original_prompt) > 80 else ""}"'
        )
        if result.action == MitigationAction.BLOCK:
            self._logger.warning(msg)
        elif result.action in (MitigationAction.SANITIZE, MitigationAction.WARN):
            self._logger.info(msg)
        else:
            self._logger.debug(msg)
