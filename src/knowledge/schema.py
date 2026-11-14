"""Pydantic schemas for clinical knowledge, rules, facts, and provenance.

Enforces:
1. Full clinical provenance for every rule.
2. Separation of clinically validated guidelines from educational prototypes.
3. Strict certainty factor boundaries [-1.0, 1.0].
4. Invariants for Emergency Override rules (cannot be weakened, highest priority).
5. Three-valued logic (TRUE, FALSE, UNKNOWN).
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from src.config import (
    CF_MAX,
    CF_MIN,
    MIN_ADULT_AGE,
    RulePriority,
    TriageUrgency,
    TruthValue,
    ValidationStatus,
)


class ComparisonOperator(str, Enum):
    """Comparison operators for rule antecedent conditions."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    IN = "in"
    NOT_IN = "not_in"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"


class ClinicalProvenance(BaseModel):
    """Metadata detailing the official medical guideline origin of a rule."""
    source_id: str = Field(..., description="Unique key for the clinical guideline document.")
    source_title: str = Field(..., description="Full official title of the guideline.")
    organization: str = Field(..., description="Publishing body (e.g., WHO, NICE, CDC).")
    guideline_identifier: str = Field(..., description="Official code or ID (e.g., NICE CG95, WHO BEC).")
    section_number: str = Field(..., description="Exact section, table, or algorithm step.")
    publication_date: str = Field(..., description="Publication or last update date/year.")
    target_population: str = Field(..., description="Target demographic (must include adults >= 18).")
    source_url: str = Field(..., description="Official online URL or DOI to the published document.")

    @field_validator("target_population")
    @classmethod
    def validate_target_population(cls, v: str) -> str:
        if "adult" not in v.lower() and "18" not in v:
            raise ValueError(
                f"Target population '{v}' must explicitly specify applicability to adults (18+)."
            )
        return v


class Antecedent(BaseModel):
    """A single conditional test in an IF-THEN rule premise."""
    fact_name: str = Field(..., description="Identifier of the clinical observation or vital sign.")
    operator: ComparisonOperator = Field(
        default=ComparisonOperator.EQUALS,
        description="Logical comparison operator."
    )
    expected_value: Any = Field(
        default=None,
        description="Value to compare against (ignored for IS_TRUE / IS_FALSE)."
    )
    required_truth_value: TruthValue = Field(
        default=TruthValue.TRUE,
        description="Expected truth value. If fact is UNKNOWN, condition fails/remains unknown."
    )


class Consequent(BaseModel):
    """Action or conclusion asserted when a rule fires."""
    target_attribute: str = Field(
        ...,
        description="Attribute to assert in working memory (e.g. 'triage_urgency' or intermediate flag)."
    )
    target_value: Any = Field(
        ...,
        description="Value to assert (e.g., TriageUrgency.EMERGENCY or boolean True)."
    )
    urgency_level: Optional[TriageUrgency] = Field(
        default=None,
        description="Direct triage classification, if this consequent determines urgency."
    )
    clinical_action: str = Field(
        ...,
        description="Recommended immediate clinical next step (e.g. 'Call emergency ambulance 112 / 108')."
    )
    clinical_rationale: str = Field(
        ...,
        description="Concise medical reasoning explaining why this condition mandates this action."
    )


class TriageRule(BaseModel):
    """A production rule implementing an IF-THEN clinical triage heuristic."""
    rule_id: str = Field(..., description="Unique alphanumeric identifier (e.g. 'WHO_BEC_AIRWAY_01').")
    name: str = Field(..., description="Human-readable title of the rule.")
    description: str = Field(..., description="Detailed clinical description.")
    category: str = Field(..., description="Clinical subsystem: emergency_override, respiratory, cardiovascular, etc.")
    priority: RulePriority = Field(
        default=RulePriority.MEDIUM,
        description="Evaluation priority. Higher priority rules evaluate first."
    )
    is_emergency_override: bool = Field(
        default=False,
        description="If True, rule short-circuits standard inference and cannot be weakened."
    )
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.CLINICALLY_VALIDATED,
        description="Must be explicitly flagged as clinically validated or educationally demonstrated."
    )
    source_id: str = Field(..., description="Reference matching a ClinicalProvenance entry.")
    section_number: str = Field(..., description="Specific section from the source guideline.")
    antecedents: List[Antecedent] = Field(..., min_length=1, description="List of premise conditions (AND conjunction).")
    consequent: Consequent = Field(..., description="The triage conclusion and action.")
    rule_cf: float = Field(
        default=1.0,
        ge=CF_MIN,
        le=CF_MAX,
        description="Rule certainty factor CF(H, E) in [-1.0, +1.0]."
    )

    @model_validator(mode="after")
    def validate_emergency_override_invariants(self) -> "TriageRule":
        """Safety Invariant: Emergency overrides must have highest priority and absolute certainty."""
        if self.is_emergency_override:
            if self.priority != RulePriority.EMERGENCY_OVERRIDE:
                raise ValueError(
                    f"Rule '{self.rule_id}' is marked as emergency override but has priority {self.priority}. "
                    f"Must be RulePriority.EMERGENCY_OVERRIDE (100)."
                )
            if self.consequent.urgency_level != TriageUrgency.EMERGENCY:
                raise ValueError(
                    f"Rule '{self.rule_id}' is an emergency override but assigns urgency {self.consequent.urgency_level}. "
                    f"Must assign TriageUrgency.EMERGENCY."
                )
            if abs(self.rule_cf - 1.0) > 1e-6:
                raise ValueError(
                    f"Rule '{self.rule_id}' is an emergency override with rule_cf={self.rule_cf}. "
                    f"Emergency overrides cannot be weakened and must have rule_cf=1.0."
                )
        return self


class Fact(BaseModel):
    """A clinical observation, sign, or vital measurement in working memory.
    
    Adheres strictly to three-valued logic (TRUE, FALSE, UNKNOWN).
    """
    name: str = Field(..., description="Canonical fact identifier (e.g. 'stridor', 'systolic_bp').")
    value: Any = Field(default=None, description="Scalar value (e.g., 88, 120.5, 'severe', or True/False).")
    truth_value: TruthValue = Field(
        default=TruthValue.TRUE,
        description="Epistemic status: TRUE, FALSE, or UNKNOWN."
    )
    cf: float = Field(
        default=1.0,
        ge=CF_MIN,
        le=CF_MAX,
        description="Observation certainty factor in [-1.0, +1.0]. Definite evidence has cf=1.0."
    )
    source_attribution: str = Field(
        default="patient_report",
        description="Source of this observation (e.g. 'triage_nurse', 'patient_report', 'vital_monitor')."
    )
    recorded_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_known(self) -> bool:
        """True if the fact has been evaluated as TRUE or FALSE (not missing/UNKNOWN)."""
        return self.truth_value != TruthValue.UNKNOWN

    @property
    def is_true(self) -> bool:
        """True only if the epistemic state is explicitly TRUE."""
        return self.truth_value == TruthValue.TRUE

    @property
    def is_false(self) -> bool:
        """True only if the epistemic state is explicitly FALSE."""
        return self.truth_value == TruthValue.FALSE
