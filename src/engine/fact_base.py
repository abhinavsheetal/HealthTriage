"""Working memory (FactBase) managing patient observations and inferred facts.

Implements:
- Three-valued epistemic states (TRUE, FALSE, UNKNOWN).
- Strict non-assumption rule: Missing facts are UNKNOWN, never FALSE.
- Antecedent evaluation with CF propagation.
- Duplicate evidence detection and evidence updating.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from src.config import CF_MAX, CF_MIN, FLOAT_TOLERANCE, TruthValue
from src.engine.certainty import combine_cfs
from src.knowledge.schema import Antecedent, ComparisonOperator, Fact


class FactBase:
    """Working memory storing known facts, vitals, and intermediate conclusions."""

    def __init__(self):
        self._facts: Dict[str, Fact] = {}
        self._evidence_history: List[Fact] = []

    def set_fact(self, fact: Fact) -> None:
        """Store or update a fact in working memory."""
        self._facts[fact.name] = deepcopy(fact)
        self._evidence_history.append(deepcopy(fact))

    def add_observation(
        self,
        name: str,
        value: Any = None,
        truth_value: TruthValue = TruthValue.TRUE,
        cf: float = 1.0,
        source_attribution: str = "patient_report",
    ) -> Fact:
        """Add or update an observation with certainty factor and truth state."""
        fact = Fact(
            name=name,
            value=value,
            truth_value=truth_value,
            cf=cf,
            source_attribution=source_attribution,
            recorded_at=datetime.now(),
        )
        self.set_fact(fact)
        return fact

    def get_fact(self, name: str) -> Fact:
        """Retrieve a fact from working memory.
        
        CRITICAL INVARIANT:
        If the fact has not been asserted, it returns an UNKNOWN fact.
        Missing data is NEVER defaulted to FALSE.
        """
        if name in self._facts:
            return self._facts[name]
        return Fact(
            name=name,
            value=None,
            truth_value=TruthValue.UNKNOWN,
            cf=0.0,
            source_attribution="unrecorded_missing",
        )

    def has_fact(self, name: str) -> bool:
        """Check if a fact has been explicitly asserted with a known truth state."""
        if name not in self._facts:
            return False
        return self._facts[name].is_known

    def all_facts(self) -> Dict[str, Fact]:
        """Return a copy of all stored facts."""
        return deepcopy(self._facts)

    def known_facts(self) -> Dict[str, Fact]:
        """Return only facts whose truth value is known (TRUE or FALSE)."""
        return {k: deepcopy(v) for k, v in self._facts.items() if v.is_known}

    def combine_fact_evidence(self, new_fact: Fact) -> Fact:
        """Combine incoming independent evidence for an existing fact using MYCIN algebra."""
        if new_fact.name not in self._facts:
            self.set_fact(new_fact)
            return self._facts[new_fact.name]

        existing = self._facts[new_fact.name]

        # If both state the same value, combine their CFs
        if existing.value == new_fact.value and existing.truth_value == new_fact.truth_value:
            combined_cf = combine_cfs(existing.cf, new_fact.cf)
            existing.cf = combined_cf
            existing.recorded_at = datetime.now()
            self._evidence_history.append(deepcopy(new_fact))
            return existing

        # If values or truth states differ, update to newer observation and record history
        self.set_fact(new_fact)
        return self._facts[new_fact.name]

    def evaluate_antecedent(self, antecedent: Antecedent) -> Tuple[bool, float, str]:
        """Evaluate a single rule antecedent against current working memory.
        
        Returns:
            Tuple[is_satisfied: bool, premise_cf: float, reasoning_detail: str]
        
        Invariant:
            If fact is UNKNOWN, condition evaluates to False with CF=0.0 (missing != false).
        """
        fact = self.get_fact(antecedent.fact_name)

        # 1. Check epistemic state
        if fact.truth_value == TruthValue.UNKNOWN:
            return False, 0.0, f"Fact '{antecedent.fact_name}' is UNKNOWN (missing data)."

        op = antecedent.operator
        val = fact.value
        target = antecedent.expected_value

        # Handle boolean presence / absence checks under three-valued logic
        if target is False or op == ComparisonOperator.IS_FALSE:
            # Requires fact to be explicitly known and FALSE (absence of symptom)
            if fact.truth_value == TruthValue.FALSE or val is False:
                return True, fact.cf, f"Fact '{fact.name}' is explicitly FALSE (absent)."
            else:
                return False, 0.0, f"Fact '{fact.name}' is TRUE, but condition requires FALSE (absence)."

        if target is True or op == ComparisonOperator.IS_TRUE:
            # Requires fact to be explicitly known and TRUE (presence of symptom)
            if fact.truth_value == TruthValue.TRUE and val is not False:
                return True, fact.cf, f"Fact '{fact.name}' is TRUE."
            else:
                return False, 0.0, f"Fact '{fact.name}' is FALSE, but condition requires TRUE."

        # If antecedent explicitly specified a required truth value for non-boolean observations
        if antecedent.required_truth_value and fact.truth_value != antecedent.required_truth_value:
            return (
                False,
                0.0,
                f"Fact '{antecedent.fact_name}' truth value {fact.truth_value} "
                f"!= required {antecedent.required_truth_value}.",
            )

        satisfied = False
        detail = ""

        try:
            if op == ComparisonOperator.IS_TRUE:
                satisfied = fact.is_true and (val is True or val == 1 or val is not None)
                detail = f"Fact '{fact.name}' is TRUE."
            elif op == ComparisonOperator.IS_FALSE:
                satisfied = fact.is_false
                detail = f"Fact '{fact.name}' is FALSE."
            elif op == ComparisonOperator.EQUALS:
                satisfied = (val == target)
                detail = f"'{fact.name}' ({val}) == {target}"
            elif op == ComparisonOperator.NOT_EQUALS:
                satisfied = (val != target)
                detail = f"'{fact.name}' ({val}) != {target}"
            elif op == ComparisonOperator.LESS_THAN:
                satisfied = (float(val) < float(target))
                detail = f"'{fact.name}' ({val}) < {target}"
            elif op == ComparisonOperator.LESS_THAN_OR_EQUAL:
                satisfied = (float(val) <= float(target))
                detail = f"'{fact.name}' ({val}) <= {target}"
            elif op == ComparisonOperator.GREATER_THAN:
                satisfied = (float(val) > float(target))
                detail = f"'{fact.name}' ({val}) > {target}"
            elif op == ComparisonOperator.GREATER_THAN_OR_EQUAL:
                satisfied = (float(val) >= float(target))
                detail = f"'{fact.name}' ({val}) >= {target}"
            elif op == ComparisonOperator.IN:
                satisfied = (val in target)
                detail = f"'{fact.name}' ({val}) in {target}"
            elif op == ComparisonOperator.NOT_IN:
                satisfied = (val not in target)
                detail = f"'{fact.name}' ({val}) not in {target}"
            else:
                return False, 0.0, f"Unsupported comparison operator: {op}"
        except (TypeError, ValueError) as exc:
            return False, 0.0, f"Comparison error on '{antecedent.fact_name}': {exc}"

        if satisfied:
            # The certainty of this satisfied antecedent is the certainty of the underlying observation
            return True, fact.cf, detail
        else:
            return False, 0.0, f"Condition failed: {detail}"

    def clone(self) -> "FactBase":
        """Produce an independent deep copy of this working memory."""
        new_fb = FactBase()
        new_fb._facts = deepcopy(self._facts)
        new_fb._evidence_history = deepcopy(self._evidence_history)
        return new_fb
