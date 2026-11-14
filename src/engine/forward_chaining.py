"""Forward Chaining Inference Engine.

Implements:
- Data-driven iterative production rule matching.
- Conflict resolution:
    1. Priority-first (RulePriority descending).
    2. Specificity (number of antecedents descending).
    3. Refractoriness (each rule fires at most once per execution cycle).
    4. Most-restrictive urgency dominance for clinical safety.
- Conjunction CF calculus (min of premise CFs).
- Rule CF propagation (premise_cf * rule_cf).
- Hypothesis evidence combination via classical MYCIN algebra.
- Detailed iteration-by-iteration audit logging to Explainer.
"""

from typing import Dict, List, Optional, Set, Tuple

from src.config import (
    CF_THRESHOLD_ACTIVE,
    RulePriority,
    TriageUrgency,
    TruthValue,
)
from src.engine.certainty import combine_cfs, conjunction_cf, propagate_cf
from src.engine.explainer import (
    AntecedentMatchTrace,
    AuditTrail,
    ForwardIterationTrace,
    RuleFiringTrace,
    RuleRejectionTrace,
)
from src.engine.fact_base import FactBase
from src.knowledge.loader import RuleKnowledgeBase
from src.knowledge.schema import Fact, TriageRule


class ForwardChainingEngine:
    """Forward-chaining inference engine over declarative clinical production rules."""

    def __init__(self, knowledge_base: RuleKnowledgeBase, max_cycles: int = 50):
        self.kb = knowledge_base
        self.max_cycles = max_cycles
        # Only standard (non-emergency-override) rules participate in regular chaining
        self.rules: List[TriageRule] = self.kb.get_standard_rules()

    def run(
        self,
        fact_base: FactBase,
        audit_trail: Optional[AuditTrail] = None,
    ) -> Tuple[FactBase, Dict[TriageUrgency, float], Optional[TriageRule]]:
        """Execute forward chaining until a fixed point is reached.
        
        Returns:
            Tuple[updated_fact_base, urgency_cfs_dict, dominant_firing_rule]
        """
        fired_rule_ids: Set[str] = set()
        urgency_hypotheses: Dict[TriageUrgency, float] = {}
        dominant_rule: Optional[TriageRule] = None

        cycle = 0
        while cycle < self.max_cycles:
            cycle += 1
            cycle_fired_any = False

            iteration_trace = ForwardIterationTrace(iteration_number=cycle)

            # Conflict Resolution: Sort candidate rules by priority desc, then specificity desc
            candidate_rules = sorted(
                self.rules,
                key=lambda r: (r.priority, len(r.antecedents)),
                reverse=True,
            )

            for rule in candidate_rules:
                iteration_trace.considered_rules.append(rule.rule_id)

                # Refractoriness check: Rule already fired
                if rule.rule_id in fired_rule_ids:
                    iteration_trace.rejections.append(
                        RuleRejectionTrace(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            reason="refractory",
                            details="Rule has already fired in a previous iteration cycle.",
                        )
                    )
                    continue

                # Antecedent evaluation
                antecedent_traces: List[AntecedentMatchTrace] = []
                premise_cfs: List[float] = []
                antecedents_satisfied = True

                for antecedent in rule.antecedents:
                    satisfied, cf_val, detail = fact_base.evaluate_antecedent(antecedent)
                    trace = AntecedentMatchTrace(
                        fact_name=antecedent.fact_name,
                        condition_detail=detail,
                        observation_cf=cf_val,
                        satisfied=satisfied,
                    )
                    antecedent_traces.append(trace)

                    if not satisfied:
                        antecedents_satisfied = False
                        iteration_trace.rejections.append(
                            RuleRejectionTrace(
                                rule_id=rule.rule_id,
                                rule_name=rule.name,
                                reason="antecedent_failed",
                                details=f"Condition failed: {detail}",
                            )
                        )
                        break
                    else:
                        premise_cfs.append(cf_val)

                if not antecedents_satisfied:
                    continue

                # Calculate premise CF using conjunction (min)
                premise_cf = conjunction_cf(premise_cfs)

                # Propagation check: Premise must be positive
                if premise_cf <= 0.0:
                    iteration_trace.rejections.append(
                        RuleRejectionTrace(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            reason="cf_below_threshold",
                            details=f"Conjunction premise CF={premise_cf:.2f} is <= 0.0.",
                        )
                    )
                    continue

                # Propagate rule CF
                propagated_cf = propagate_cf(premise_cf, rule.rule_cf)

                # Consequent Assertion & Evidence Combination
                consequent = rule.consequent
                prior_cf: Optional[float] = None
                new_combined_cf = propagated_cf

                if consequent.urgency_level:
                    urgency = consequent.urgency_level
                    if urgency in urgency_hypotheses:
                        prior_cf = urgency_hypotheses[urgency]
                        new_combined_cf = combine_cfs(prior_cf, propagated_cf)
                    urgency_hypotheses[urgency] = new_combined_cf

                # Assert consequent fact into working memory
                fact_base.add_observation(
                    name=consequent.target_attribute,
                    value=consequent.target_value,
                    truth_value=TruthValue.TRUE,
                    cf=new_combined_cf,
                    source_attribution=f"inferred_by_{rule.rule_id}",
                )

                # Fetch guideline provenance for trace
                prov = self.kb.sources.get(rule.source_id)
                prov_dict = {
                    "source_id": rule.source_id,
                    "title": prov.source_title if prov else rule.source_id,
                    "organization": prov.organization if prov else "Unknown",
                    "section": rule.section_number,
                    "url": prov.source_url if prov else "",
                }

                firing_trace = RuleFiringTrace(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category,
                    priority=rule.priority,
                    validation_status=rule.validation_status.value,
                    antecedent_traces=antecedent_traces,
                    premise_cf=premise_cf,
                    rule_cf=rule.rule_cf,
                    propagated_cf=propagated_cf,
                    consequent_attribute=consequent.target_attribute,
                    consequent_value=consequent.target_value,
                    prior_hypothesis_cf=prior_cf,
                    combined_hypothesis_cf=new_combined_cf,
                    clinical_action=consequent.clinical_action,
                    clinical_rationale=consequent.clinical_rationale,
                    source_id=rule.source_id,
                    section_number=rule.section_number,
                    provenance=prov_dict,
                )

                iteration_trace.firings.append(firing_trace)
                iteration_trace.new_facts_asserted.append(
                    f"{consequent.target_attribute} = {consequent.target_value} (CF={new_combined_cf:.2f})"
                )

                fired_rule_ids.add(rule.rule_id)
                cycle_fired_any = True

                # Keep track of the highest priority / acuity rule
                if dominant_rule is None:
                    dominant_rule = rule
                elif rule.priority > dominant_rule.priority:
                    dominant_rule = rule

            if audit_trail:
                audit_trail.add_forward_iteration(iteration_trace)

            # If no rules fired in this cycle, we have reached a fixed point
            if not cycle_fired_any:
                break

        return fact_base, urgency_hypotheses, dominant_rule
