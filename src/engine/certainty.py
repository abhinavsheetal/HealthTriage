"""Classical MYCIN Certainty Factor (CF) algebra implementation.

Mathematical specifications:
1. CF domain: [-1.0, +1.0]
2. Conjunction (AND): min(CF_1, CF_2, ...)
3. Disjunction (OR): max(CF_1, CF_2, ...)
4. Negation (NOT): -CF
5. Rule propagation: CF(H, E) = CF(E) * CF(rule) if CF(E) > 0 else 0.0
6. Combination of independent evidence:
   - If CF_1 >= 0 and CF_2 >= 0:
       CF_comb = CF_1 + CF_2 * (1 - CF_1)
   - If CF_1 < 0 and CF_2 < 0:
       CF_comb = CF_1 + CF_2 * (1 + CF_1)
   - If CF_1 * CF_2 < 0:
       CF_comb = (CF_1 + CF_2) / (1 - min(|CF_1|, |CF_2|))
   - Contradictory boundary (CF_1 = +1.0, CF_2 = -1.0):
       Explicitly detected as ContradictoryEvidenceError.
"""

from typing import Iterable, List, Sequence
from src.config import CF_MAX, CF_MIN, FLOAT_TOLERANCE


class CertaintyFactorError(Exception):
    """Base exception for certainty factor calculation errors."""
    pass


class ContradictoryEvidenceError(CertaintyFactorError):
    """Raised when contradictory absolute evidence (+1.0 and -1.0) is combined."""
    def __init__(self, message: str = "Contradictory absolute certainty combined (CF=+1.0 and CF=-1.0)."):
        super().__init__(message)


def clamp_cf(value: float) -> float:
    """Clamp value to [-1.0, 1.0] within floating point tolerance."""
    if abs(value - CF_MAX) <= FLOAT_TOLERANCE:
        return CF_MAX
    if abs(value - CF_MIN) <= FLOAT_TOLERANCE:
        return CF_MIN
    if value > CF_MAX:
        raise ValueError(f"Certainty factor {value} exceeds upper bound {CF_MAX}")
    if value < CF_MIN:
        raise ValueError(f"Certainty factor {value} is below lower bound {CF_MIN}")
    return round(value, 8)


def conjunction_cf(cfs: Sequence[float]) -> float:
    """Calculate the Certainty Factor of an AND conjunction: min(CF_1, ..., CF_n).
    
    Empty sequence returns 0.0.
    """
    if not cfs:
        return 0.0
    for cf in cfs:
        clamp_cf(cf)
    return min(cfs)


def disjunction_cf(cfs: Sequence[float]) -> float:
    """Calculate the Certainty Factor of an OR disjunction: max(CF_1, ..., CF_n).
    
    Empty sequence returns 0.0.
    """
    if not cfs:
        return 0.0
    for cf in cfs:
        clamp_cf(cf)
    return max(cfs)


def negation_cf(cf: float) -> float:
    """Calculate the Certainty Factor of a NOT negation: -CF."""
    valid_cf = clamp_cf(cf)
    return clamp_cf(-valid_cf)


def propagate_cf(premise_cf: float, rule_cf: float) -> float:
    """Calculate the propagated Certainty Factor for a rule conclusion.
    
    Classical MYCIN Rule Propagation:
    - If premise_cf > 0: CF(conclusion) = premise_cf * rule_cf
    - If premise_cf <= 0: CF(conclusion) = 0.0
      (In MYCIN, disbelieved or unevidenced premises do not fire a rule)
    """
    p_cf = clamp_cf(premise_cf)
    r_cf = clamp_cf(rule_cf)

    if p_cf <= 0.0:
        return 0.0

    return clamp_cf(p_cf * r_cf)


def combine_cfs(cf1: float, cf2: float) -> float:
    """Combine two independent Certainty Factors for the same hypothesis.
    
    Follows the classical Shortliffe & Buchanan MYCIN combination formula.
    """
    c1 = clamp_cf(cf1)
    c2 = clamp_cf(cf2)

    # Identity element: combining with 0 yields the other CF
    if abs(c1) < FLOAT_TOLERANCE:
        return c2
    if abs(c2) < FLOAT_TOLERANCE:
        return c1

    # Absolute contradictory evidence (+1.0 and -1.0)
    if (abs(c1 - 1.0) < FLOAT_TOLERANCE and abs(c2 - (-1.0)) < FLOAT_TOLERANCE) or \
       (abs(c1 - (-1.0)) < FLOAT_TOLERANCE and abs(c2 - 1.0) < FLOAT_TOLERANCE):
        raise ContradictoryEvidenceError(
            f"Cannot combine mutually contradictory absolute evidence: CF1={c1}, CF2={c2}"
        )

    # Case 1: Both positive (reinforcing belief)
    if c1 > 0.0 and c2 > 0.0:
        result = c1 + c2 * (1.0 - c1)
        return clamp_cf(result)

    # Case 2: Both negative (reinforcing disbelief)
    if c1 < 0.0 and c2 < 0.0:
        result = c1 + c2 * (1.0 + c1)
        return clamp_cf(result)

    # Case 3: Conflicting signs (one positive, one negative)
    denominator = 1.0 - min(abs(c1), abs(c2))
    if abs(denominator) < FLOAT_TOLERANCE:
        raise ContradictoryEvidenceError(
            f"Denominator zero in conflicting evidence combination: CF1={c1}, CF2={c2}"
        )
    result = (c1 + c2) / denominator
    return clamp_cf(result)


def combine_multiple_cfs(cfs: Iterable[float]) -> float:
    """Combine an arbitrary sequence of independent CFs for the same hypothesis.
    
    Applies pairwise combination sequentially: (...((cf_1 + cf_2) + cf_3) + ...).
    Empty sequence returns 0.0.
    """
    cf_list = list(cfs)
    if not cf_list:
        return 0.0

    accumulated = clamp_cf(cf_list[0])
    for next_cf in cf_list[1:]:
        accumulated = combine_cfs(accumulated, next_cf)

    return accumulated
