"""Backward Chaining Inference Engine.

Implements:
- Goal-directed recursive hypothesis evaluation.
- Separate recursive search identifying missing evidence required to prove a goal.
- Cycle detection via active goal stack.
- CF combination across multiple rule pathways supporting the same hypothesis.
- Independent from UI, generating rich explanation traces.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from src.config import CF_THRESHOLD_ACTIVE, TruthValue
from src.engine.certainty import combine_cfs, conjunction_cf, propagate_cf
from src.engine.explainer import AuditTrail, BackwardGoalTrace
from src.engine.fact_base import FactBase
from src.knowledge.loader import RuleKnowledgeBase
from src.knowledge.schema import Antecedent, TriageRule


class BackwardChainingEngine:
    """Recursive goal-driven inference engine for preliminary triage hypotheses."""

    def __init__(self, knowledge_base: RuleKnowledgeBase):
        self.kb = knowledge_base
        self.all_rules: List[TriageRule] = self.kb.rules

    def prove_goal(
        self,
        goal_attribute: str,
        goal_value: Any,
        fact_base: FactBase,
        audit_trail: Optional[AuditTrail] = None,
    ) -> BackwardGoalTrace:
        """Evaluate whether a specific clinical goal is supported by current working memory.
        
        Args:
            goal_attribute: Attribute to test (e.g. 'triage_urgency' or intermediate flag).
            goal_value: Expected value (e.g. TriageUrgency.EMERGENCY or True).
            fact_base: Working memory with current facts.
            audit_trail: Optional audit trail to append traces.
        """
        active_goal_stack: Set[str] = set()
        trace = self._prove_recursive(
            goal_attribute=goal_attribute,
            goal_value=goal_value,
            fact_base=fact_base,
            goal_stack=active_goal_stack,
            depth=0,
        )

        if audit_trail:
            audit_trail.add_backward_trace(trace)

        return trace

    def _prove_recursive(
        self,
        goal_attribute: str,
        goal_value: Any,
        fact_base: FactBase,
        goal_stack: Set[str],
        depth: int,
    ) -> BackwardGoalTrace:
        goal_signature = f"{goal_attribute}=={goal_value}"

        # Initialize trace node
        trace = BackwardGoalTrace(
            goal_attribute=goal_attribute,
            goal_value=goal_value,
            proved=False,
            final_cf=0.0,
            call_stack_depth=depth,
        )

        # 1. Cycle detection
        if goal_signature in goal_stack:
            return trace

        # 2. Check if already known in FactBase
        existing_fact = fact_base.get_fact(goal_attribute)
        if existing_fact.is_known:
            if existing_fact.value == goal_value or str(existing_fact.value) == str(goal_value):
                if existing_fact.cf > 0.0:
                    trace.proved = True
                    trace.final_cf = existing_fact.cf
                    return trace

        # 3. Find candidate rules that conclude this goal
        candidate_rules = self._find_candidate_rules(goal_attribute, goal_value)
        trace.rules_evaluated = [r.rule_id for r in candidate_rules]

        if not candidate_rules:
            # Atomic patient observation: if missing, record as required missing evidence
            if not existing_fact.is_known:
                trace.missing_facts_required.append(goal_attribute)
            return trace

        goal_stack.add(goal_signature)

        combined_cf: Optional[float] = None
        missing_accum: Set[str] = set()

        for rule in candidate_rules:
            rule_antecedents_satisfied = True
            premise_cfs: List[float] = []

            for antecedent in rule.antecedents:
                fact_name = antecedent.fact_name
                # Check if this antecedent can be deduced by other rules (subgoal)
                sub_candidates = self._find_candidate_rules(fact_name, antecedent.expected_value)

                if sub_candidates and not fact_base.has_fact(fact_name):
                    # Recursive subgoal evaluation
                    sub_trace = self._prove_recursive(
                        goal_attribute=fact_name,
                        goal_value=antecedent.expected_value,
                        fact_base=fact_base,
                        goal_stack=goal_stack,
                        depth=depth + 1,
                    )
                    trace.subgoal_traces.append(sub_trace)
                    missing_accum.update(sub_trace.missing_facts_required)

                    if sub_trace.proved and sub_trace.final_cf > 0.0:
                        premise_cfs.append(sub_trace.final_cf)
                    else:
                        rule_antecedents_satisfied = False
                        break
                else:
                    # Evaluate atomic fact against FactBase
                    satisfied, cf_val, _ = fact_base.evaluate_antecedent(antecedent)
                    if satisfied:
                        premise_cfs.append(cf_val)
                    else:
                        rule_antecedents_satisfied = False
                        # If fact is UNKNOWN, record as missing evidence required
                        if fact_base.get_fact(fact_name).truth_value == TruthValue.UNKNOWN:
                            missing_accum.add(fact_name)
                        break

            if rule_antecedents_satisfied and premise_cfs:
                premise_cf = conjunction_cf(premise_cfs)
                if premise_cf > 0.0:
                    propagated = propagate_cf(premise_cf, rule.rule_cf)
                    trace.supporting_rules.append(rule.rule_id)

                    if combined_cf is None:
                        combined_cf = propagated
                    else:
                        combined_cf = combine_cfs(combined_cf, propagated)

        goal_stack.remove(goal_signature)

        trace.missing_facts_required = sorted(list(missing_accum))

        if combined_cf is not None and combined_cf >= CF_THRESHOLD_ACTIVE:
            trace.proved = True
            trace.final_cf = combined_cf

        return trace

    def _find_candidate_rules(self, attribute: str, value: Any) -> List[TriageRule]:
        """Find all rules that conclude the target attribute and value."""
        candidates = []
        for r in self.all_rules:
            # Check target attribute match
            if r.consequent.target_attribute == attribute:
                if r.consequent.target_value == value or str(r.consequent.target_value) == str(value):
                    candidates.append(r)
                    continue

            # Check urgency level match
            if attribute == "triage_urgency" and r.consequent.urgency_level:
                if r.consequent.urgency_level == value or str(r.consequent.urgency_level.value) == str(value):
                    candidates.append(r)

        # Sort candidate rules by priority desc
        return sorted(candidates, key=lambda r: r.priority, reverse=True)
