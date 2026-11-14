"""Explainable AI (XAI) and Audit Trail subsystem.

Records:
- Input patient observations and vitals.
- Emergency override evaluation (short-circuiting).
- Considered, matched, rejected, and fired rules.
- Certainty Factor calculations at each step (conjunction, propagation, combination).
- Complete clinical guideline citations for every inference step.
- Goal-directed backward chaining hypothesis exploration trees.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config import TriageUrgency
from src.knowledge.schema import ClinicalProvenance, Fact, TriageRule


@dataclass
class AntecedentMatchTrace:
    fact_name: str
    condition_detail: str
    observation_cf: float
    satisfied: bool


@dataclass
class RuleRejectionTrace:
    rule_id: str
    rule_name: str
    reason: str  # e.g., "antecedent_failed", "refractory_already_fired", "cf_below_threshold"
    details: str


@dataclass
class RuleFiringTrace:
    rule_id: str
    rule_name: str
    category: str
    priority: int
    validation_status: str
    antecedent_traces: List[AntecedentMatchTrace]
    premise_cf: float
    rule_cf: float
    propagated_cf: float
    consequent_attribute: str
    consequent_value: Any
    prior_hypothesis_cf: Optional[float]
    combined_hypothesis_cf: float
    clinical_action: str
    clinical_rationale: str
    source_id: str
    section_number: str
    provenance: Optional[Dict[str, str]] = None


@dataclass
class ForwardIterationTrace:
    iteration_number: int
    considered_rules: List[str] = field(default_factory=list)
    rejections: List[RuleRejectionTrace] = field(default_factory=list)
    firings: List[RuleFiringTrace] = field(default_factory=list)
    new_facts_asserted: List[str] = field(default_factory=list)


@dataclass
class BackwardGoalTrace:
    goal_attribute: str
    goal_value: Any
    proved: bool
    final_cf: float
    rules_evaluated: List[str] = field(default_factory=list)
    supporting_rules: List[str] = field(default_factory=list)
    missing_facts_required: List[str] = field(default_factory=list)
    call_stack_depth: int = 0
    subgoal_traces: List["BackwardGoalTrace"] = field(default_factory=list)


class AuditTrail:
    """Comprehensive trace log recording all reasoning across inference engines."""

    def __init__(self):
        self.timestamp: datetime = datetime.now()
        self.initial_observations: Dict[str, Any] = {}
        self.emergency_override_triggered: bool = False
        self.emergency_override_trace: Optional[Dict[str, Any]] = None
        self.forward_iterations: List[ForwardIterationTrace] = []
        self.fired_rules: List[RuleFiringTrace] = []
        self.backward_traces: List[BackwardGoalTrace] = []
        self.final_urgency: Optional[TriageUrgency] = None
        self.final_cf: float = 0.0
        self.primary_action: str = ""
        self.primary_rationale: str = ""

    def record_initial_facts(self, facts: Dict[str, Fact]) -> None:
        self.initial_observations = {
            name: {
                "value": f.value,
                "truth_value": f.truth_value.value,
                "cf": f.cf,
                "source": f.source_attribution,
            }
            for name, f in facts.items()
        }

    def record_emergency_override(
        self,
        rule: TriageRule,
        matched_conditions: List[str],
        provenance: Optional[ClinicalProvenance] = None,
    ) -> None:
        self.emergency_override_triggered = True
        self.emergency_override_trace = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "category": rule.category,
            "priority": rule.priority,
            "cf": 1.0,
            "matched_conditions": matched_conditions,
            "clinical_action": rule.consequent.clinical_action,
            "clinical_rationale": rule.consequent.clinical_rationale,
            "source_id": rule.source_id,
            "section_number": rule.section_number,
            "guideline": provenance.source_title if provenance else rule.source_id,
            "organization": provenance.organization if provenance else "Unknown",
            "source_url": provenance.source_url if provenance else "",
        }

    def add_forward_iteration(self, iteration: ForwardIterationTrace) -> None:
        self.forward_iterations.append(iteration)
        for firing in iteration.firings:
            self.fired_rules.append(firing)

    def add_backward_trace(self, trace: BackwardGoalTrace) -> None:
        self.backward_traces.append(trace)

    def set_final_outcome(
        self,
        urgency: TriageUrgency,
        cf: float,
        action: str,
        rationale: str,
    ) -> None:
        self.final_urgency = urgency
        self.final_cf = cf
        self.primary_action = action
        self.primary_rationale = rationale

    def generate_narrative_explanation(self) -> str:
        """Produce a human-readable clinical rationale narrative."""
        if self.emergency_override_triggered and self.emergency_override_trace:
            trace = self.emergency_override_trace
            conditions_str = "; ".join(trace.get("matched_conditions", []))
            return (
                f"🚨 EMERGENCY OVERRIDE ACTIVATED: Immediate high-priority triage assigned based on "
                f"danger signs ({conditions_str}). "
                f"Rule '{trace['rule_name']}' fired at absolute certainty (CF=1.0) under "
                f"{trace['organization']} {trace['guideline']} ({trace['section_number']}). "
                f"Mandatory action: {trace['clinical_action']}"
            )

        if not self.fired_rules:
            return (
                f"Preliminary triage evaluated as {self.final_urgency.value if self.final_urgency else 'STANDARD'} "
                f"(CF={self.final_cf:.2f}). No emergency override or high-acuity production rules triggered. "
                f"Routine observation or self-care protocols apply with standard safety-netting."
            )

        narratives = [
            f"Preliminary triage determined urgency as {self.final_urgency.value} "
            f"with an aggregate Certainty Factor of {self.final_cf:.2f}."
        ]
        narratives.append(f"A total of {len(self.fired_rules)} production rule(s) fired:")

        for idx, firing in enumerate(self.fired_rules, 1):
            prov_text = f"[{firing.source_id} {firing.section_number}]"
            narratives.append(
                f"{idx}. {firing.rule_name} (Priority {firing.priority}, Propagated CF={firing.propagated_cf:.2f}): "
                f"{firing.clinical_rationale} {prov_text}"
            )

        narratives.append(f"Primary Clinical Action: {self.primary_action}")
        return "\n".join(narratives)
