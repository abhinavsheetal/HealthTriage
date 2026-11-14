"""Emergency Override Engine.

Executes deterministically BEFORE normal forward/backward chaining.
Safety Invariants:
1. Short-circuits standard inference if any red-flag emergency rule fires.
2. Emergency override rules must NEVER be weakened or attenuated by Certainty Factor calculations.
   Concluded CF is strictly 1.0 (absolute clinical directive).
"""

from dataclasses import dataclass, field
from typing import List, Optional

from src.config import TriageUrgency
from src.engine.fact_base import FactBase
from src.knowledge.loader import RuleKnowledgeBase
from src.knowledge.schema import TriageRule


@dataclass
class EmergencyOverrideResult:
    """Outcome of the pre-inference emergency red-flag screening."""
    triggered: bool
    fired_rule: Optional[TriageRule] = None
    urgency: Optional[TriageUrgency] = None
    clinical_action: Optional[str] = None
    clinical_rationale: Optional[str] = None
    matched_conditions: List[str] = field(default_factory=list)
    cf: float = 1.0

    @property
    def is_emergency(self) -> bool:
        return self.triggered and self.urgency == TriageUrgency.EMERGENCY


class EmergencyOverrideEngine:
    """Evaluates emergency override production rules prior to standard inference."""

    def __init__(self, knowledge_base: RuleKnowledgeBase):
        self.kb = knowledge_base
        self.emergency_rules: List[TriageRule] = self.kb.get_emergency_overrides()

    def evaluate(self, fact_base: FactBase) -> EmergencyOverrideResult:
        """Scan working memory against all emergency override rules.
        
        Rules are evaluated in order of priority (descending) and specificity (descending).
        The first fully satisfied emergency override immediately short-circuits.
        """
        # Sort by priority desc, then number of antecedents (specificity) desc
        sorted_rules = sorted(
            self.emergency_rules,
            key=lambda r: (r.priority, len(r.antecedents)),
            reverse=True,
        )

        for rule in sorted_rules:
            matched_conditions: List[str] = []
            all_antecedents_satisfied = True

            for antecedent in rule.antecedents:
                satisfied, _, detail = fact_base.evaluate_antecedent(antecedent)
                if satisfied:
                    matched_conditions.append(detail)
                else:
                    all_antecedents_satisfied = False
                    break

            if all_antecedents_satisfied:
                # Critical Safety Circuit-Breaker: Emergency override triggered!
                # CF is strictly 1.0 and is NEVER weakened.
                return EmergencyOverrideResult(
                    triggered=True,
                    fired_rule=rule,
                    urgency=TriageUrgency.EMERGENCY,
                    clinical_action=rule.consequent.clinical_action,
                    clinical_rationale=rule.consequent.clinical_rationale,
                    matched_conditions=matched_conditions,
                    cf=1.0,
                )

        return EmergencyOverrideResult(triggered=False)
