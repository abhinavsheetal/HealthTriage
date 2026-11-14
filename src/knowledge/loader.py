"""Knowledge base loader and validator.

Loads clinical sources and production rules from JSON files, enforcing:
- Structural Pydantic validation.
- Cross-reference integrity (rule source_id must exist in clinical sources).
- Rule ID uniqueness.
- Strict clinical scope (adult population only, urgency classification only).
- Invariants for emergency overrides.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from src.config import MIN_ADULT_AGE, RulePriority, TriageUrgency, ValidationStatus
from src.knowledge.schema import ClinicalProvenance, TriageRule


class KnowledgeBaseValidationError(Exception):
    """Raised when rule or source validation fails."""
    pass


def load_clinical_sources(sources_path: Union[str, Path]) -> Dict[str, ClinicalProvenance]:
    """Load and validate clinical sources catalog from a JSON file."""
    path = Path(sources_path)
    if not path.is_file():
        raise FileNotFoundError(f"Clinical sources file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise KnowledgeBaseValidationError(
            f"Expected clinical sources root to be a JSON object, got {type(data).__name__}"
        )

    sources: Dict[str, ClinicalProvenance] = {}
    for source_key, entry in data.items():
        try:
            provenance = ClinicalProvenance(**entry)
            sources[provenance.source_id] = provenance
        except Exception as e:
            raise KnowledgeBaseValidationError(
                f"Error validating clinical source '{source_key}': {e}"
            ) from e

    return sources


def load_rules_from_file(
    file_path: Union[str, Path],
    sources: Dict[str, ClinicalProvenance],
    existing_rule_ids: Optional[Set[str]] = None,
) -> List[TriageRule]:
    """Load and validate a list of triage rules from a single JSON file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Rule file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise KnowledgeBaseValidationError(
            f"Expected rule file '{path.name}' to contain a JSON array, got {type(data).__name__}"
        )

    seen_ids = existing_rule_ids if existing_rule_ids is not None else set()
    rules: List[TriageRule] = []

    for idx, rule_data in enumerate(data):
        rule_id = rule_data.get("rule_id", f"INDEX_{idx}")
        if rule_id in seen_ids:
            raise KnowledgeBaseValidationError(
                f"Duplicate rule_id detected: '{rule_id}' in file {path.name}"
            )

        # Cross-reference source_id
        source_id = rule_data.get("source_id")
        if not source_id or source_id not in sources:
            raise KnowledgeBaseValidationError(
                f"Rule '{rule_id}' references unknown or missing source_id: '{source_id}'."
            )

        try:
            rule = TriageRule(**rule_data)
        except Exception as e:
            raise KnowledgeBaseValidationError(
                f"Validation error in rule '{rule_id}' ({path.name}): {e}"
            ) from e

        seen_ids.add(rule.rule_id)
        rules.append(rule)

    return rules


def load_all_rules(
    rules_dir: Union[str, Path],
    sources: Dict[str, ClinicalProvenance],
) -> List[TriageRule]:
    """Load and validate all JSON rule files from a directory."""
    path = Path(rules_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"Rules directory not found: {path}")

    seen_ids: Set[str] = set()
    all_rules: List[TriageRule] = []

    json_files = sorted(path.glob("*.json"))
    if not json_files:
        raise KnowledgeBaseValidationError(f"No .json rule files found in {path}")

    for json_file in json_files:
        rules = load_rules_from_file(json_file, sources, existing_rule_ids=seen_ids)
        all_rules.extend(rules)

    return all_rules


class RuleKnowledgeBase:
    """In-memory validated repository of clinical sources and triage rules."""

    def __init__(self, sources: Dict[str, ClinicalProvenance], rules: List[TriageRule]):
        self.sources = sources
        self.rules = rules
        self._rules_by_id: Dict[str, TriageRule] = {r.rule_id: r for r in rules}

    @classmethod
    def from_directory(
        cls,
        sources_file: Union[str, Path],
        rules_dir: Union[str, Path],
    ) -> "RuleKnowledgeBase":
        """Factory method to load and validate a complete knowledge base."""
        sources = load_clinical_sources(sources_file)
        rules = load_all_rules(rules_dir, sources)
        return cls(sources, rules)

    def get_rule(self, rule_id: str) -> Optional[TriageRule]:
        """Fetch a single rule by its unique ID."""
        return self._rules_by_id.get(rule_id)

    def get_emergency_overrides(self) -> List[TriageRule]:
        """Return all emergency override rules sorted by priority descending."""
        return sorted(
            [r for r in self.rules if r.is_emergency_override],
            key=lambda r: r.priority,
            reverse=True,
        )

    def get_standard_rules(self) -> List[TriageRule]:
        """Return non-override rules sorted by priority descending."""
        return sorted(
            [r for r in self.rules if not r.is_emergency_override],
            key=lambda r: r.priority,
            reverse=True,
        )

    def get_rules_by_category(self, category: str) -> List[TriageRule]:
        """Filter rules by clinical category."""
        return [r for r in self.rules if r.category == category]

    def get_rules_by_validation(self, status: ValidationStatus) -> List[TriageRule]:
        """Filter rules by clinical validation status."""
        return [r for r in self.rules if r.validation_status == status]

    def __len__(self) -> int:
        return len(self.rules)
