"""Global configuration, clinical domain enumerations, and mathematical constants.

All definitions strictly enforce preliminary triage boundaries:
- Urgency classification only; disease diagnosis is explicitly out of scope.
- Three-valued logic (TRUE, FALSE, UNKNOWN) for fact states.
- Adults aged 18 and above only.
"""

from enum import Enum, IntEnum


class TriageUrgency(str, Enum):
    """Standardized urgency tiers for preliminary health triage.
    
    Reflects standard international emergency/ambulatory triage acuity levels
    (e.g., Manchester Triage System, Emergency Severity Index, WHO BEC).
    These represent recommended time-to-evaluation, NOT specific disease diagnoses.
    """
    EMERGENCY = "EMERGENCY"         # Immediate emergency care / Resuscitation (0 mins)
    VERY_URGENT = "VERY_URGENT"     # Highly urgent / Assessment within 10-60 mins
    URGENT = "URGENT"               # Urgent care / Assessment within 2-12 hours (same day)
    STANDARD = "STANDARD"           # Non-urgent / Primary care consultation within 24-72 hours
    SELF_CARE = "SELF_CARE"         # Self-care with safety-netting / symptom monitoring

    @property
    def severity_rank(self) -> int:
        """Numeric rank for conflict resolution (higher = more critical/restrictive)."""
        ranks = {
            TriageUrgency.EMERGENCY: 5,
            TriageUrgency.VERY_URGENT: 4,
            TriageUrgency.URGENT: 3,
            TriageUrgency.STANDARD: 2,
            TriageUrgency.SELF_CARE: 1,
        }
        return ranks[self]


class TruthValue(str, Enum):
    """Three-valued logic states for patient observations and rule evaluations.
    
    CRITICAL CLINICAL INVARIANT:
    Missing information must NEVER be assumed to be FALSE.
    If an observation has not been provided or evaluated, it is UNKNOWN.
    """
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class ValidationStatus(str, Enum):
    """Distinguishes clinically validated guidelines from educational prototypes."""
    CLINICALLY_VALIDATED = "clinically_validated"
    EDUCATIONALLY_DEMONSTRATED = "educationally_demonstrated"


class RulePriority(IntEnum):
    """Rule priority levels for conflict resolution during forward/backward chaining.
    
    Emergency overrides execute at Priority 100 before any standard rules.
    """
    EMERGENCY_OVERRIDE = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25


# Clinical Scope Constants
MIN_ADULT_AGE: int = 18
TARGET_POPULATION: str = "Adults aged 18 and above"

# Certainty Factor Bounds (MYCIN Standard)
CF_MIN: float = -1.0
CF_MAX: float = 1.0
CF_THRESHOLD_ACTIVE: float = 0.2  # Threshold below which belief is too weak to assert
FLOAT_TOLERANCE: float = 1e-7
