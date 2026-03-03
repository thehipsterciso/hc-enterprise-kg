"""Cross-entity coherence rules for the Enrichment Agency.

Defines validation rules that ensure data integrity across entity
relationships in the knowledge graph. Each rule checks a specific
cross-entity invariant and can optionally remediate violations.

Rules are used by the CoherenceEnricher (enrichers/coherence_enricher.py)
during post-enrichment validation passes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph


class CoherenceSeverity(StrEnum):
    """Severity levels for coherence violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class CoherenceViolation:
    """A single coherence violation found during validation."""

    rule_id: str
    severity: CoherenceSeverity
    affected_entities: list[str] = field(default_factory=list)
    description: str = ""
    remediation: str = ""


class CoherenceRule(ABC):
    """Base class for cross-entity coherence rules."""

    RULE_ID: str = ""
    DESCRIPTION: str = ""

    @abstractmethod
    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        """Check the rule and return any violations found."""
        ...

    def remediate(
        self, kg: KnowledgeGraph, violation: CoherenceViolation
    ) -> bool:
        """Attempt to fix a violation. Returns True if fixed."""
        return False


# ---------------------------------------------------------------------------
# Rule 1: Person skills should align with Role requirements
# ---------------------------------------------------------------------------


class PersonSkillsAlignWithRole(CoherenceRule):
    """Person's skill_inventory should include skills from their Role's required_skills."""

    RULE_ID = "COHERENCE-001"
    DESCRIPTION = "Person skills align with assigned Role requirements"

    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        from domain.base import EntityType, RelationshipType

        violations: list[CoherenceViolation] = []
        people = kg.list_entities(EntityType.PERSON)

        for person in people:
            person_dict = person.model_dump() if hasattr(person, "model_dump") else {}
            skills_inv = person_dict.get("skill_inventory") or []
            person_skills = {
                s.get("skill_name", "").lower()
                for s in skills_inv
                if isinstance(s, dict)
            }
            if not person_skills:
                continue

            roles = kg.neighbors(
                person.id, direction="out",
                relationship_type=RelationshipType.HAS_ROLE,
            )
            for role in roles:
                role_dict = role.model_dump() if hasattr(role, "model_dump") else {}
                required = role_dict.get("required_skills") or []
                required_names = {
                    (r.get("skill_name", "") if isinstance(r, dict) else str(r)).lower()
                    for r in required
                }
                missing = required_names - person_skills
                if missing and len(missing) > len(required_names) * 0.5:
                    violations.append(CoherenceViolation(
                        rule_id=self.RULE_ID,
                        severity=CoherenceSeverity.WARNING,
                        affected_entities=[person.id, role.id],
                        description=(
                            f"Person '{person.name}' missing >50% of required skills "
                            f"for role '{role.name}': {missing}"
                        ),
                        remediation="Add missing skills to person's skill_inventory",
                    ))
        return violations


# ---------------------------------------------------------------------------
# Rule 2: System cost correlates with criticality
# ---------------------------------------------------------------------------


class SystemCostMatchesCriticality(CoherenceRule):
    """System annual_cost should correlate with criticality level."""

    RULE_ID = "COHERENCE-002"
    DESCRIPTION = "System cost correlates with criticality tier"

    COST_THRESHOLDS = {
        "critical": 50_000,
        "high": 20_000,
        "medium": 5_000,
        "low": 0,
    }

    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        from domain.base import EntityType

        violations: list[CoherenceViolation] = []
        systems = kg.list_entities(EntityType.SYSTEM)

        for system in systems:
            d = system.model_dump() if hasattr(system, "model_dump") else {}
            cost = d.get("annual_cost")
            criticality = (d.get("criticality") or "").lower()
            if cost is None or not criticality:
                continue

            threshold = self.COST_THRESHOLDS.get(criticality, 0)
            if cost < threshold:
                violations.append(CoherenceViolation(
                    rule_id=self.RULE_ID,
                    severity=CoherenceSeverity.WARNING,
                    affected_entities=[system.id],
                    description=(
                        f"System '{system.name}' has criticality='{criticality}' "
                        f"but annual_cost=${cost:,.0f} (expected >=${threshold:,.0f})"
                    ),
                    remediation=f"Adjust annual_cost to >= ${threshold:,.0f}",
                ))
        return violations


# ---------------------------------------------------------------------------
# Rule 3: Vendor risk correlates with contract value
# ---------------------------------------------------------------------------


class VendorRiskMatchesContractValue(CoherenceRule):
    """Vendor risk_level should reflect total contract exposure."""

    RULE_ID = "COHERENCE-003"
    DESCRIPTION = "Vendor risk level correlates with contract value"

    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        from domain.base import EntityType, RelationshipType

        violations: list[CoherenceViolation] = []
        vendors = kg.list_entities(EntityType.VENDOR)

        for vendor in vendors:
            vd = vendor.model_dump() if hasattr(vendor, "model_dump") else {}
            risk_level = (vd.get("risk_level") or vd.get("vendor_risk_tier") or "").lower()

            contracts = kg.neighbors(
                vendor.id, direction="both",
                relationship_type=RelationshipType.CONTRACTS_WITH,
            )
            total_value = 0.0
            for contract in contracts:
                cd = contract.model_dump() if hasattr(contract, "model_dump") else {}
                val = cd.get("total_value") or cd.get("contract_value") or 0
                if isinstance(val, (int, float)):
                    total_value += val

            if total_value > 500_000 and risk_level in ("low", "minimal"):
                violations.append(CoherenceViolation(
                    rule_id=self.RULE_ID,
                    severity=CoherenceSeverity.ERROR,
                    affected_entities=[vendor.id],
                    description=(
                        f"Vendor '{vendor.name}' has risk_level='{risk_level}' "
                        f"but total contract value=${total_value:,.0f}"
                    ),
                    remediation="Reassess vendor risk given contract exposure",
                ))
        return violations


# ---------------------------------------------------------------------------
# Rule 4: Control effectiveness correlates with risk residual
# ---------------------------------------------------------------------------


class ControlEffectivenessMatchesRiskResidual(CoherenceRule):
    """Control effectiveness should correlate with mitigated risk residual level."""

    RULE_ID = "COHERENCE-004"
    DESCRIPTION = "Control effectiveness correlates with risk residual level"

    RISK_ORDERING = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        from domain.base import EntityType, RelationshipType

        violations: list[CoherenceViolation] = []
        controls = kg.list_entities(EntityType.CONTROL)

        for control in controls:
            cd = control.model_dump() if hasattr(control, "model_dump") else {}
            effectiveness = (cd.get("effectiveness_rating") or "").lower()
            if effectiveness not in ("effective", "highly_effective"):
                continue

            mitigated_risks = kg.neighbors(
                control.id, direction="out",
                relationship_type=RelationshipType.MITIGATES,
            )
            for risk in mitigated_risks:
                rd = risk.model_dump() if hasattr(risk, "model_dump") else {}
                residual = (rd.get("residual_risk_level") or "").lower()
                if self.RISK_ORDERING.get(residual, 0) >= 3:
                    violations.append(CoherenceViolation(
                        rule_id=self.RULE_ID,
                        severity=CoherenceSeverity.WARNING,
                        affected_entities=[control.id, risk.id],
                        description=(
                            f"Control '{control.name}' rated '{effectiveness}' "
                            f"but mitigated risk '{risk.name}' has "
                            f"residual_level='{residual}'"
                        ),
                        remediation=(
                            "Either downgrade control effectiveness "
                            "or re-evaluate risk residual level"
                        ),
                    ))
        return violations


# ---------------------------------------------------------------------------
# Rule 5: Temporal consistency across entities
# ---------------------------------------------------------------------------


class TemporalConsistency(CoherenceRule):
    """Temporal fields should be chronologically consistent."""

    RULE_ID = "COHERENCE-005"
    DESCRIPTION = "Temporal fields are chronologically consistent"

    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        violations: list[CoherenceViolation] = []
        all_entities = kg.list_entities()

        for entity in all_entities:
            if entity.valid_from and entity.valid_until:
                if entity.valid_from > entity.valid_until:
                    violations.append(CoherenceViolation(
                        rule_id=self.RULE_ID,
                        severity=CoherenceSeverity.ERROR,
                        affected_entities=[entity.id],
                        description=(
                            f"Entity '{entity.name}' has valid_from > valid_until"
                        ),
                        remediation="Swap valid_from and valid_until",
                    ))

            if entity.created_at and entity.updated_at:
                if entity.created_at > entity.updated_at:
                    violations.append(CoherenceViolation(
                        rule_id=self.RULE_ID,
                        severity=CoherenceSeverity.WARNING,
                        affected_entities=[entity.id],
                        description=(
                            f"Entity '{entity.name}' has created_at > updated_at"
                        ),
                        remediation="Set updated_at >= created_at",
                    ))
        return violations


# ---------------------------------------------------------------------------
# Rule 6: Data classification consistency across flows
# ---------------------------------------------------------------------------


class DataClassificationConsistency(CoherenceRule):
    """Data classification should be consistent across connected data flows."""

    RULE_ID = "COHERENCE-006"
    DESCRIPTION = "Data classification consistent across data flows"

    CLASSIFICATION_ORDER = {
        "public": 1, "internal": 2, "confidential": 3,
        "restricted": 4, "top_secret": 5,
    }

    def validate(self, kg: KnowledgeGraph) -> list[CoherenceViolation]:
        from domain.base import EntityType, RelationshipType

        violations: list[CoherenceViolation] = []
        flows = kg.list_entities(EntityType.DATA_FLOW)

        for flow in flows:
            fd = flow.model_dump() if hasattr(flow, "model_dump") else {}
            flow_classification = (fd.get("classification") or "").lower()
            encryption = fd.get("encryption_in_transit", False)

            if (
                flow_classification in ("restricted", "confidential")
                and not encryption
            ):
                violations.append(CoherenceViolation(
                    rule_id=self.RULE_ID,
                    severity=CoherenceSeverity.ERROR,
                    affected_entities=[flow.id],
                    description=(
                        f"DataFlow '{flow.name}' classified as "
                        f"'{flow_classification}' but encryption_in_transit=False"
                    ),
                    remediation="Enable encryption_in_transit for sensitive flows",
                ))
        return violations


# ---------------------------------------------------------------------------
# Registry of all coherence rules
# ---------------------------------------------------------------------------

ALL_COHERENCE_RULES: list[CoherenceRule] = [
    PersonSkillsAlignWithRole(),
    SystemCostMatchesCriticality(),
    VendorRiskMatchesContractValue(),
    ControlEffectivenessMatchesRiskResidual(),
    TemporalConsistency(),
    DataClassificationConsistency(),
]


def validate_all_rules(kg: KnowledgeGraph) -> list[CoherenceViolation]:
    """Run all coherence rules and return all violations."""
    violations: list[CoherenceViolation] = []
    for rule in ALL_COHERENCE_RULES:
        violations.extend(rule.validate(kg))
    return violations
