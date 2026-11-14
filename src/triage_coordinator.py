"""Triage Coordinator: Central Orchestration Layer.

Connects:
- KnowledgeBase (validated clinical production rules & provenance).
- FactBase (working memory with three-valued truth logic).
- EmergencyOverrideEngine (priority-0 deterministic safety circuit-breaker).
- ForwardChainingEngine (data-driven inference & conflict resolution).
- BackwardChainingEngine (goal-driven recursive hypothesis testing).
- AuditTrail (complete explainability & clinical citation logs).

Enforces:
1. Adult population boundary check (age >= 18).
2. Emergency override rules execute first and are never weakened by CF algebra.
3. Most-restrictive urgency dominance for patient safety.
4. Statutory non-diagnostic clinical disclaimer.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import (
    CF_THRESHOLD_ACTIVE,
    MIN_ADULT_AGE,
    TARGET_POPULATION,
    TriageUrgency,
    TruthValue,
)
from src.engine.backward_chaining import BackwardChainingEngine
from src.engine.emergency_override import EmergencyOverrideEngine
from src.engine.explainer import AuditTrail, BackwardGoalTrace
from src.engine.fact_base import FactBase
from src.engine.forward_chaining import ForwardChainingEngine
from src.knowledge.loader import RuleKnowledgeBase
from src.knowledge.schema import Fact, TriageRule

CLINICAL_DISCLAIMER: str = (
    "CLINICAL DECISION SUPPORT NOTICE (NON-DIAGNOSTIC): "
    "This system provides preliminary acuity triage recommendation based on rule-based "
    "clinical guidelines (WHO BEC, NICE CG95, NICE NG51). It is strictly an educational and "
    "triaging assistance tool, NOT a definitive diagnostic instrument. "
    "It does not replace clinical judgment, in-person physical examination, or emergency medical services. "
    "If a patient exhibits signs of life-threatening distress, call emergency services (112 / 108 in India) immediately."
)


@dataclass
class TriageResult:
    """Unified result container returned by the Triage Coordinator."""
    patient_age: int
    is_adult: bool
    is_out_of_scope: bool
    scope_message: str
    overall_urgency: TriageUrgency
    overall_cf: float
    primary_action: str
    primary_rationale: str
    is_emergency_override: bool
    override_rule_id: Optional[str]
    all_concluded_urgencies: Dict[TriageUrgency, float]
    fired_rules: List[TriageRule]
    audit_trail: AuditTrail
    concluded_facts: Dict[str, Fact]
    disclaimer: str = CLINICAL_DISCLAIMER


class TriageCoordinator:
    """Coordinates the entire triage reasoning pipeline."""

    def __init__(self, knowledge_base: RuleKnowledgeBase):
        self.kb = knowledge_base
        self.emergency_engine = EmergencyOverrideEngine(self.kb)
        self.forward_engine = ForwardChainingEngine(self.kb)
        self.backward_engine = BackwardChainingEngine(self.kb)

    @classmethod
    def from_paths(
        cls,
        sources_path: Union[str, Path],
        rules_dir: Union[str, Path],
    ) -> "TriageCoordinator":
        """Initialize coordinator directly from sources and rules paths."""
        kb = RuleKnowledgeBase.from_directory(sources_path, rules_dir)
        return cls(kb)

    def evaluate_patient(
        self,
        age: int,
        observations: Dict[str, Any],
        observation_cfs: Optional[Dict[str, float]] = None,
    ) -> TriageResult:
        """Run complete triage evaluation over patient presentation.
        
        Args:
            age: Patient age in years.
            observations: Dict of fact names to values (or Booleans).
            observation_cfs: Optional Dict of fact names to certainty factors [-1.0, 1.0].
        """
        audit_trail = AuditTrail()
        observation_cfs = observation_cfs or {}

        # 1. Demographic & Clinical Scope Enforcement
        if age < MIN_ADULT_AGE:
            scope_msg = (
                f"PATIENT OUT OF SCOPE: Age {age} is below minimum adult threshold ({MIN_ADULT_AGE}). "
                "This system is calibrated strictly for adults aged 18 and older. "
                "Pediatric physiological thresholds differ substantially. "
                "Please refer immediately to pediatric emergency guidelines (e.g., WHO ETAT Pediatric)."
            )
            audit_trail.set_final_outcome(
                urgency=TriageUrgency.EMERGENCY,
                cf=1.0,
                action="Transfer immediately to a specialized pediatric triage service.",
                rationale=scope_msg,
            )
            return TriageResult(
                patient_age=age,
                is_adult=False,
                is_out_of_scope=True,
                scope_message=scope_msg,
                overall_urgency=TriageUrgency.EMERGENCY,
                overall_cf=1.0,
                primary_action="Transfer to pediatric facility or call emergency services.",
                primary_rationale=scope_msg,
                is_emergency_override=True,
                override_rule_id="SCOPE_VIOLATION_PEDIATRIC",
                all_concluded_urgencies={TriageUrgency.EMERGENCY: 1.0},
                fired_rules=[],
                audit_trail=audit_trail,
                concluded_facts={},
            )

        # 2. Build Working Memory (FactBase)
        fact_base = FactBase()
        for name, val in observations.items():
            cf_val = observation_cfs.get(name, 1.0)
            if val is not None:
                # Truth state: if boolean False, record FALSE; otherwise TRUE
                truth_state = TruthValue.FALSE if val is False else TruthValue.TRUE
                fact_base.add_observation(
                    name=name,
                    value=val,
                    truth_value=truth_state,
                    cf=cf_val,
                    source_attribution="patient_presentation",
                )

        audit_trail.record_initial_facts(fact_base.all_facts())

        # 3. Emergency Override Phase (Priority 0 Circuit-Breaker)
        override_result = self.emergency_engine.evaluate(fact_base)
        if override_result.triggered and override_result.fired_rule:
            rule = override_result.fired_rule
            prov = self.kb.sources.get(rule.source_id)
            audit_trail.record_emergency_override(
                rule=rule,
                matched_conditions=override_result.matched_conditions,
                provenance=prov,
            )
            audit_trail.set_final_outcome(
                urgency=TriageUrgency.EMERGENCY,
                cf=1.0,  # Never weakened
                action=override_result.clinical_action or "",
                rationale=override_result.clinical_rationale or "",
            )
            return TriageResult(
                patient_age=age,
                is_adult=True,
                is_out_of_scope=False,
                scope_message="Patient meets adult demographic scope.",
                overall_urgency=TriageUrgency.EMERGENCY,
                overall_cf=1.0,
                primary_action=override_result.clinical_action or "",
                primary_rationale=override_result.clinical_rationale or "",
                is_emergency_override=True,
                override_rule_id=rule.rule_id,
                all_concluded_urgencies={TriageUrgency.EMERGENCY: 1.0},
                fired_rules=[rule],
                audit_trail=audit_trail,
                concluded_facts=fact_base.all_facts(),
            )

        # 4. Forward Chaining Phase (Data-Driven Inference)
        updated_fact_base, urgency_cfs, dominant_rule = self.forward_engine.run(
            fact_base=fact_base,
            audit_trail=audit_trail,
        )

        # 5. Conflict Resolution: Most-Restrictive Urgency Dominance
        fired_rules: List[TriageRule] = []
        for firing in audit_trail.fired_rules:
            r = self.kb.get_rule(firing.rule_id)
            if r:
                fired_rules.append(r)

        if urgency_cfs:
            # Sort concluded urgencies by severity rank descending
            sorted_urgencies = sorted(
                urgency_cfs.items(),
                key=lambda item: (item[0].severity_rank, item[1]),
                reverse=True,
            )
            dominant_urgency, dominant_cf = sorted_urgencies[0]

            if dominant_rule:
                action = dominant_rule.consequent.clinical_action
                rationale = dominant_rule.consequent.clinical_rationale
            else:
                action = f"Clinical assessment recommended within the timeframe for {dominant_urgency.value} acuity."
                rationale = f"Acuity inferred through combination of clinical findings."
        else:
            # No high-acuity rules triggered
            dominant_urgency = TriageUrgency.STANDARD
            dominant_cf = 0.50
            action = "Routine primary care consultation or self-monitoring with safety netting."
            rationale = "No emergency red flags or urgent criteria triggered from the reported findings."

        audit_trail.set_final_outcome(
            urgency=dominant_urgency,
            cf=dominant_cf,
            action=action,
            rationale=rationale,
        )

        return TriageResult(
            patient_age=age,
            is_adult=True,
            is_out_of_scope=False,
            scope_message="Patient meets adult demographic scope.",
            overall_urgency=dominant_urgency,
            overall_cf=dominant_cf,
            primary_action=action,
            primary_rationale=rationale,
            is_emergency_override=False,
            override_rule_id=None,
            all_concluded_urgencies=urgency_cfs,
            fired_rules=fired_rules,
            audit_trail=audit_trail,
            concluded_facts=updated_fact_base.all_facts(),
        )

    def prove_hypothesis(
        self,
        goal_attribute: str,
        goal_value: Any,
        observations: Dict[str, Any],
        observation_cfs: Optional[Dict[str, float]] = None,
    ) -> BackwardGoalTrace:
        """Run backward chaining to determine if a specific clinical hypothesis holds."""
        fact_base = FactBase()
        observation_cfs = observation_cfs or {}
        for name, val in observations.items():
            cf_val = observation_cfs.get(name, 1.0)
            if val is not None:
                truth = TruthValue.FALSE if val is False else TruthValue.TRUE
                fact_base.add_observation(
                    name=name,
                    value=val,
                    truth_value=truth,
                    cf=cf_val,
                )

        return self.backward_engine.prove_goal(
            goal_attribute=goal_attribute,
            goal_value=goal_value,
            fact_base=fact_base,
        )
