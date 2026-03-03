"""Coherence enricher — validates and remediates cross-entity coherence violations.

This enricher identifies and fixes structural inconsistencies across the knowledge
graph, such as:
- Skill alignment between Person and Role
- Cost correlation with System criticality
- Temporal ordering violations
- Classification consistency across DataFlows
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from domain.base import BaseEntity, EntityType


class CoherenceSeverity(StrEnum):
    """Severity levels for coherence violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CoherenceViolation:
    """Represents a single coherence violation detected in the graph."""

    rule_id: str
    violation_type: str
    severity: CoherenceSeverity
    affected_entities: list[str]
    description: str
    remediation: str
    recommended_fix: dict[str, Any] = field(default_factory=dict)


class CoherenceEnricher:
    """Validates and remediates cross-entity coherence in the knowledge graph.

    This enricher implements six coherence rules:
    1. Person.skills aligns with Role.required_skills
    2. System.annual_cost correlates with system criticality
    3. Vendor.risk_level correlates with contract value and data access
    4. Control.effectiveness correlates with Risk.residual_level
    5. Temporal fields are chronologically consistent
    6. Data classifications are consistent across DataFlows

    Usage:
        enricher = CoherenceEnricher()
        violations = enricher.validate_coherence(kg)
        fixed_count = enricher.remediate(kg, violations)
    """

    # Severity thresholds for cost/criticality correlation.
    CRITICALITY_COST_MAP = {
        "critical": (50000, None),  # Min annual cost for critical systems.
        "high": (20000, None),
        "medium": (5000, None),
        "low": (0, 20000),
    }

    # Risk level to contract value correlation.
    RISK_CONTRACT_MAP = {
        "critical": (100000, None),
        "high": (50000, None),
        "medium": (10000, None),
        "low": (0, 50000),
    }

    def __init__(self):
        """Initialize the coherence enricher."""
        self.violations: list[CoherenceViolation] = []

    def validate_coherence(
        self,
        kg: object,  # KnowledgeGraph
    ) -> list[CoherenceViolation]:
        """Validate cross-entity coherence across the entire graph.

        Args:
            kg: The KnowledgeGraph instance.

        Returns:
            List of CoherenceViolation objects found.
        """
        self.violations = []

        # Collect entities by type for efficient checking.
        entities_by_type = {}
        if hasattr(kg, "get_entities"):
            for entity_type in EntityType:
                entities = kg.get_entities(entity_type)
                if entities:
                    entities_by_type[entity_type] = {e.id: e for e in entities}

        # Run each coherence rule.
        if EntityType.PERSON in entities_by_type:
            self._validate_person_role_skill_alignment(
                kg,
                entities_by_type,
            )

        if EntityType.SYSTEM in entities_by_type:
            self._validate_system_cost_criticality_correlation(
                kg,
                entities_by_type,
            )

        if EntityType.VENDOR in entities_by_type:
            self._validate_vendor_risk_contract_correlation(
                kg,
                entities_by_type,
            )

        if EntityType.CONTROL in entities_by_type and EntityType.RISK in entities_by_type:
            self._validate_control_risk_effectiveness_correlation(
                kg,
                entities_by_type,
            )

        self._validate_temporal_consistency(kg, entities_by_type)
        self._validate_data_classification_consistency(kg, entities_by_type)

        return self.violations

    def remediate(
        self,
        kg: object,
        violations: list[CoherenceViolation],
    ) -> int:
        """Remediate coherence violations.

        Args:
            kg: The KnowledgeGraph instance.
            violations: List of violations to fix.

        Returns:
            Count of successfully remediated violations.
        """
        fixed = 0

        for violation in violations:
            if not violation.recommended_fix:
                continue

            # Get affected entity and apply updates.
            if violation.affected_entities and hasattr(kg, "get_entity"):
                entity_id = violation.affected_entities[0]
                entity = kg.get_entity(entity_id)

                if entity and hasattr(kg, "update_entity"):
                    try:
                        kg.update_entity(entity_id, violation.recommended_fix)
                        fixed += 1
                    except Exception:
                        pass  # Silently skip failed remediations.

        return fixed

    def _validate_person_role_skill_alignment(
        self,
        kg: object,
        entities_by_type: dict[EntityType, dict[str, BaseEntity]],
    ) -> None:
        """Rule 1: Person.skills should align with Role.required_skills."""
        persons = entities_by_type.get(EntityType.PERSON, {})
        roles = entities_by_type.get(EntityType.ROLE, {})

        if not persons or not roles:
            return

        # Get relationships between persons and roles.
        person_roles = {}
        if hasattr(kg, "get_relationships"):
            for rel in kg.get_relationships():
                if (
                    rel.relationship_type == "has_role"
                    and rel.source_id in persons
                    and rel.target_id in roles
                ):
                    person_roles.setdefault(rel.source_id, []).append(rel.target_id)

        for person_id, role_ids in person_roles.items():
            person = persons.get(person_id)
            if not person or not hasattr(person, "skills_inventory"):
                continue

            person_skills = {s.get("skill_name") for s in person.skills_inventory}

            for role_id in role_ids:
                role = roles.get(role_id)
                if not role or not hasattr(role, "required_skills"):
                    continue

                required_skills = set(role.required_skills)
                missing_skills = required_skills - person_skills

                if missing_skills:
                    self.violations.append(
                        CoherenceViolation(
                            rule_id="RULE_1",
                            violation_type="skill_gap",
                            severity=CoherenceSeverity.MEDIUM,
                            affected_entities=[person_id, role_id],
                            description=f"Person {person_id} missing skills {missing_skills} for role {role_id}",
                            remediation="Add missing skills to person or adjust role requirements",
                            recommended_fix={
                                "skills_gap_note": f"Missing: {', '.join(missing_skills)}"
                            },
                        )
                    )

    def _validate_system_cost_criticality_correlation(
        self,
        kg: object,
        entities_by_type: dict[EntityType, dict[str, BaseEntity]],
    ) -> None:
        """Rule 2: System.annual_cost should correlate with criticality."""
        systems = entities_by_type.get(EntityType.SYSTEM, {})

        if not systems:
            return

        for system_id, system in systems.items():
            if not hasattr(system, "criticality") or not hasattr(system, "annual_cost"):
                continue

            criticality = system.criticality
            annual_cost = system.annual_cost or 0

            # Check against expected range.
            min_cost, max_cost = self.CRITICALITY_COST_MAP.get(criticality, (0, None))

            if annual_cost < min_cost:
                self.violations.append(
                    CoherenceViolation(
                        rule_id="RULE_2",
                        violation_type="cost_criticality_mismatch",
                        severity=CoherenceSeverity.HIGH,
                        affected_entities=[system_id],
                        description=f"System criticality='{criticality}' but cost=${annual_cost} < minimum ${min_cost}",
                        remediation="Either increase annual cost estimate or lower criticality classification",
                        recommended_fix={
                            "annual_cost": min_cost,
                            "cost_adjustment_reason": "Coherence remediation: cost increased to match criticality",
                        },
                    )
                )
            elif max_cost and annual_cost > max_cost:
                self.violations.append(
                    CoherenceViolation(
                        rule_id="RULE_2",
                        violation_type="cost_criticality_mismatch",
                        severity=CoherenceSeverity.MEDIUM,
                        affected_entities=[system_id],
                        description=f"System criticality='{criticality}' but cost=${annual_cost} > expected ${max_cost}",
                        remediation="Either decrease annual cost or increase criticality classification",
                        recommended_fix={},
                    )
                )

    def _validate_vendor_risk_contract_correlation(
        self,
        kg: object,
        entities_by_type: dict[EntityType, dict[str, BaseEntity]],
    ) -> None:
        """Rule 3: Vendor.risk_level should correlate with contract value and data access."""
        vendors = entities_by_type.get(EntityType.VENDOR, {})
        contracts = entities_by_type.get(EntityType.CONTRACT, {})

        if not vendors or not contracts:
            return

        # Map vendors to their contracts.
        vendor_contracts = {}
        if hasattr(kg, "get_relationships"):
            for rel in kg.get_relationships():
                if (
                    rel.relationship_type == "contracts_with"
                    and rel.source_id in vendors
                    and rel.target_id in contracts
                ):
                    vendor_contracts.setdefault(rel.source_id, []).append(rel.target_id)

        for vendor_id, contract_ids in vendor_contracts.items():
            vendor = vendors.get(vendor_id)
            if not vendor or not hasattr(vendor, "risk_level"):
                continue

            total_contract_value = 0
            for contract_id in contract_ids:
                contract = contracts.get(contract_id)
                if contract and hasattr(contract, "total_value"):
                    total_contract_value += contract.total_value or 0

            risk_level = vendor.risk_level
            min_val, max_val = self.RISK_CONTRACT_MAP.get(risk_level, (0, None))

            if total_contract_value < min_val:
                self.violations.append(
                    CoherenceViolation(
                        rule_id="RULE_3",
                        violation_type="vendor_risk_value_mismatch",
                        severity=CoherenceSeverity.MEDIUM,
                        affected_entities=[vendor_id],
                        description=f"Vendor risk='{risk_level}' but contract value ${total_contract_value} < minimum ${min_val}",
                        remediation="Increase contract value or lower risk classification",
                        recommended_fix={},
                    )
                )

    def _validate_control_risk_effectiveness_correlation(
        self,
        kg: object,
        entities_by_type: dict[EntityType, dict[str, BaseEntity]],
    ) -> None:
        """Rule 4: Control.effectiveness should correlate with Risk.residual_level."""
        controls = entities_by_type.get(EntityType.CONTROL, {})
        risks = entities_by_type.get(EntityType.RISK, {})

        if not controls or not risks:
            return

        # Map controls to risks they mitigate.
        control_mitigations = {}
        if hasattr(kg, "get_relationships"):
            for rel in kg.get_relationships():
                if (
                    rel.relationship_type == "mitigates"
                    and rel.source_id in controls
                    and rel.target_id in risks
                ):
                    control_mitigations.setdefault(rel.source_id, []).append(rel.target_id)

        for control_id, risk_ids in control_mitigations.items():
            control = controls.get(control_id)
            if not control:
                continue

            control_eff = getattr(control, "control_effectiveness", {})
            eff_rating = control_eff.get("rating") if isinstance(control_eff, dict) else None

            for risk_id in risk_ids:
                risk = risks.get(risk_id)
                if not risk or not hasattr(risk, "residual_level"):
                    continue

                residual = risk.residual_level

                # High-effectiveness controls should not have high residual risk.
                if eff_rating == "effective" and residual in ("high", "critical"):
                    self.violations.append(
                        CoherenceViolation(
                            rule_id="RULE_4",
                            violation_type="control_effectiveness_mismatch",
                            severity=CoherenceSeverity.HIGH,
                            affected_entities=[control_id, risk_id],
                            description=f"Control effectiveness='{eff_rating}' but residual risk='{residual}'",
                            remediation="Either improve control effectiveness or accept higher risk",
                            recommended_fix={},
                        )
                    )

    def _validate_temporal_consistency(
        self,
        kg: object,
        entities_by_type: dict[EntityType, dict[str, BaseEntity]],
    ) -> None:
        """Rule 5: Temporal fields are chronologically consistent."""
        for entity_type, entities in entities_by_type.items():
            for entity_id, entity in entities.items():
                created_at = getattr(entity, "created_at", None)
                updated_at = getattr(entity, "updated_at", None)
                valid_from = getattr(entity, "valid_from", None)
                valid_until = getattr(entity, "valid_until", None)

                violations = []

                if created_at and updated_at and created_at > updated_at:
                    violations.append("created_at > updated_at")

                if valid_from and valid_until and valid_from > valid_until:
                    violations.append("valid_from > valid_until")

                if created_at and valid_from and created_at > valid_from:
                    violations.append("created_at > valid_from")

                if violations:
                    self.violations.append(
                        CoherenceViolation(
                            rule_id="RULE_5",
                            violation_type="temporal_ordering",
                            severity=CoherenceSeverity.HIGH,
                            affected_entities=[entity_id],
                            description=f"Temporal inconsistency: {', '.join(violations)}",
                            remediation="Correct temporal field ordering",
                            recommended_fix={"updated_at": datetime.utcnow().isoformat()},
                        )
                    )

    def _validate_data_classification_consistency(
        self,
        kg: object,
        entities_by_type: dict[EntityType, dict[str, BaseEntity]],
    ) -> None:
        """Rule 6: Data classifications are consistent across DataFlows."""
        data_flows = entities_by_type.get(EntityType.DATA_FLOW, {})

        if not data_flows:
            return

        for flow_id, flow in data_flows.items():
            if not hasattr(flow, "classification"):
                continue

            flow_class = flow.classification

            # Check source and target data assets.
            if hasattr(kg, "get_relationships"):
                for rel in kg.get_relationships():
                    if (
                        rel.source_id == flow_id
                        and rel.relationship_type == "originates_from"
                    ):
                        source = entities_by_type.get(EntityType.DATA_ASSET, {}).get(
                            rel.target_id
                        )
                        if source and hasattr(source, "classification"):
                            if source.classification != flow_class:
                                self.violations.append(
                                    CoherenceViolation(
                                        rule_id="RULE_6",
                                        violation_type="classification_mismatch",
                                        severity=CoherenceSeverity.MEDIUM,
                                        affected_entities=[flow_id, rel.target_id],
                                        description=f"DataFlow classification='{flow_class}' but source='{source.classification}'",
                                        remediation="Align classifications",
                                        recommended_fix={"classification": source.classification},
                                    )
                                )
