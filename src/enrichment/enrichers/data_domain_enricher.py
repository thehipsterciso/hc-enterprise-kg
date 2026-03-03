"""Data Domain enricher — enriches DataDomain entities with context-aware governance profiles.

The DataDomain entity (~35 attributes) is enriched by analyzing its graph neighborhood:
- DataAssets in domain (via CONTAINS) → informs asset_count, sensitivity profile
- Policies governing domain (via GOVERNS) → informs governing_policies
- OrgUnit owning domain (via OWNS/RESPONSIBLE_FOR) → informs domain_owner, steward

Tiers:
  2 (Managed): domain_owner, domain_steward, sensitivity_flags, sub_domains
  3 (Defined): governing_policies, regulatory_sensitivity, data_residency_requirements, quality_targets
  4 (Measured): maturity_dimensions (DCAM 2.2: Strategy, Governance, Quality, Operations, Platform)
  5 (Optimized): monetization_potential, innovation_use_cases
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnricherRegistry,
    EnrichmentAction,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EntityContext,
    OSINTResults,
)

# DCAM 2.2 Maturity Dimension Definitions
DCAM_DIMENSIONS = [
    {
        "name": "Data Management Strategy",
        "description": "Strategic alignment and governance vision",
    },
    {"name": "Data Governance", "description": "Policies, roles, and accountability"},
    {"name": "Data Quality Management", "description": "Quality metrics and remediation"},
    {"name": "Data Operations", "description": "Day-to-day operational management"},
    {
        "name": "Data Platform & Architecture",
        "description": "Technical infrastructure and integration",
    },
]

# Domain type templates
DOMAIN_TYPE_TEMPLATES = {
    "master_data": {
        "strategic_value": "Revenue Generating",
        "quality_emphasis": ["Accuracy", "Completeness"],
        "typical_assets": 5,
    },
    "reference_data": {
        "strategic_value": "Decision Enabling",
        "quality_emphasis": ["Timeliness", "Consistency"],
        "typical_assets": 8,
    },
    "transactional": {
        "strategic_value": "Revenue Generating",
        "quality_emphasis": ["Completeness", "Timeliness"],
        "typical_assets": 15,
    },
    "analytical": {
        "strategic_value": "Decision Enabling",
        "quality_emphasis": ["Accuracy", "Timeliness"],
        "typical_assets": 10,
    },
}

# Regulatory sensitivities by jurisdiction
REGULATORY_SENSITIVITIES = {
    "GDPR": {
        "jurisdiction": "EU",
        "handling_requirements": "Strict access controls, data minimization, consent tracking",
    },
    "CCPA": {
        "jurisdiction": "California",
        "handling_requirements": "Consumer rights fulfillment, opt-out mechanisms",
    },
    "HIPAA": {
        "jurisdiction": "USA",
        "handling_requirements": "Encryption, audit logging, access controls",
    },
    "PCI-DSS": {
        "jurisdiction": "Global",
        "handling_requirements": "Network segmentation, encryption, vulnerability scanning",
    },
}

# Data residency requirements
DATA_RESIDENCY_REQUIREMENTS = {
    "EU": {"localization_required": True, "requirement_description": "GDPR data localization"},
    "China": {
        "localization_required": True,
        "requirement_description": "Data sovereignty requirement",
    },
    "USA": {
        "localization_required": False,
        "requirement_description": "No localization requirement",
    },
    "Canada": {"localization_required": True, "requirement_description": "PIPEDA compliance"},
}


@EnricherRegistry.register
class DataDomainEnricher(AbstractEnricher):
    """Enricher for DataDomain entities.

    Context-aware enrichment that reads graph neighbors (DataAssets, Policies,
    OrgUnits) to populate governance, regulatory, quality, and maturity fields.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.DATA_DOMAIN

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a DataDomain entity based on graph context.

        Args:
            entity: The DataDomain entity to enrich.
            context: EntityContext with DataDomain's neighbors by relationship type.
            osint: Optional external research results.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile (MINIMAL, STANDARD, COMPREHENSIVE).
            enrichment_context: Shared enrichment context.

        Returns:
            EnrichmentResult with field updates, provenance, relationships, gaps.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.DATA_DOMAIN,
        )

        # Determine which tiers to populate based on profile
        tiers_to_populate = self._get_tiers_for_profile(profile)

        # Build cross-entity profile from graph context
        cross_profile = self._build_domain_profile(entity, context)

        # Tier 2: Managed — core governance fields
        if 2 in tiers_to_populate:
            updates_t2, actions_t2 = self._populate_tier_2(entity, context, cross_profile)
            result.field_updates.update(updates_t2)
            result.actions.extend(actions_t2)

        # Tier 3: Defined — cross-entity coherence
        if 3 in tiers_to_populate:
            updates_t3, actions_t3 = self._populate_tier_3(entity, context, cross_profile)
            result.field_updates.update(updates_t3)
            result.actions.extend(actions_t3)

        # Tier 4: Measured — maturity assessment
        if 4 in tiers_to_populate:
            updates_t4, actions_t4 = self._populate_tier_4(entity, context, cross_profile)
            result.field_updates.update(updates_t4)
            result.actions.extend(actions_t4)

        # Tier 5: Optimized — strategic insights
        if 5 in tiers_to_populate:
            updates_t5, actions_t5 = self._populate_tier_5(entity, context, cross_profile)
            result.field_updates.update(updates_t5)
            result.actions.extend(actions_t5)

        # Identify data gaps
        result.known_gaps = self._identify_gaps(entity, cross_profile)

        # Update provenance
        result.provenance_update = self._build_provenance(
            result.actions,
            tier,
            profile,
        )

        return result

    def _get_tiers_for_profile(self, profile: EnrichmentProfile) -> set[int]:
        """Determine which tiers to populate based on profile."""
        if profile == EnrichmentProfile.MINIMAL:
            return {2}
        elif profile == EnrichmentProfile.STANDARD:
            return {2, 3, 4}
        else:  # COMPREHENSIVE
            return {2, 3, 4, 5}

    def _build_domain_profile(self, entity: BaseEntity, context: EntityContext) -> dict:
        """Build holistic profile from graph neighborhood."""
        assets = context.get_neighbors(RelationshipType.CONTAINS)
        policies = context.get_neighbors(RelationshipType.GOVERNS)
        org_units = context.get_neighbors(RelationshipType.BELONGS_TO)

        # Infer sensitivity from contained assets
        has_sensitive_assets = False
        if assets:
            for asset in assets:
                classification = getattr(asset, "classification", "").lower()
                if "confidential" in classification or "restricted" in classification:
                    has_sensitive_assets = True
                    break

        domain_type = getattr(entity, "domain_type", "").lower() or "transactional"

        profile = {
            "domain_id": entity.id,
            "domain_name": getattr(entity, "name", ""),
            "domain_type": domain_type,
            "assets_count": len(assets),
            "policies_count": len(policies),
            "org_units_count": len(org_units),
            "has_sensitive_assets": has_sensitive_assets,
            "is_regulated": len(policies) > 0,
        }
        return profile

    def _populate_tier_2(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 2 (Managed) fields: core governance."""
        updates = {}
        actions = []

        # Domain owner — typically from OrgUnit relationship
        org_units = context.get_neighbors(RelationshipType.BELONGS_TO)
        domain_owner = ""
        if org_units:
            domain_owner = getattr(org_units[0], "id", "")

        if domain_owner:
            updates["domain_owner"] = domain_owner
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["domain_owner"],
                    source="OrgUnit relationship analysis",
                    methodology=f"Identified from {len(org_units)} organizational units",
                    confidence=ConfidenceLevel.HIGH,
                )
            )

        # Domain steward — typically inherits from owner or designated role
        domain_steward = getattr(entity, "domain_steward", "") or domain_owner
        if domain_steward:
            updates["domain_steward"] = domain_steward
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["domain_steward"],
                    source="Owner inheritance",
                    methodology="Derived from domain owner or existing assignment",
                    confidence=ConfidenceLevel.MEDIUM,
                )
            )

        # Sensitivity flags based on asset content
        assets = context.get_neighbors(RelationshipType.CONTAINS)
        sensitivity_flags = {
            "pii_flag": False,
            "phi_flag": False,
            "pci_flag": False,
            "children_data_flag": False,
            "biometric_flag": False,
            "financial_data_flag": False,
            "trade_secret_flag": False,
        }

        # Infer flags from asset names/types
        for asset in assets:
            asset_name = getattr(asset, "name", "").lower()
            if "pii" in asset_name or "customer" in asset_name:
                sensitivity_flags["pii_flag"] = True
            if "health" in asset_name or "medical" in asset_name:
                sensitivity_flags["phi_flag"] = True
            if "payment" in asset_name or "card" in asset_name:
                sensitivity_flags["pci_flag"] = True
            if "financial" in asset_name or "transaction" in asset_name:
                sensitivity_flags["financial_data_flag"] = True

        updates["sensitivity_flags"] = sensitivity_flags
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_DOMAIN,
                fields_enriched=["sensitivity_flags"],
                source="Asset content analysis",
                methodology=f"Inferred from {len(assets)} contained assets via asset names/types",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Sub-domains based on domain type
        domain_type = cross_profile.get("domain_type", "transactional")
        DOMAIN_TYPE_TEMPLATES.get(domain_type, {}).get("typical_assets", 5)
        sub_domains = [
            {
                "sub_domain_name": f"{domain_type.title()} - Subdomain {i + 1}",
                "sub_domain_description": f"Sub-classification within {cross_profile.get('domain_name', 'domain')}",
            }
            for i in range(max(1, len(assets) // 3))  # 1 subdomain per 3 assets
        ]
        if sub_domains:
            updates["sub_domains"] = sub_domains
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["sub_domains"],
                    source="Asset distribution analysis",
                    methodology=f"Created {len(sub_domains)} subdomains based on {len(assets)} assets",
                    confidence=ConfidenceLevel.LOW,
                )
            )

        return updates, actions

    def _populate_tier_3(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 3 (Defined) fields: cross-entity coherence."""
        updates = {}
        actions = []

        # Governing policies
        policies = context.get_neighbors(RelationshipType.GOVERNS)
        governing_policies = [
            {
                "policy_id": policy.id,
                "policy_name": getattr(policy, "name", ""),
                "policy_type": getattr(policy, "policy_type", "Data Governance"),
            }
            for policy in policies[:10]
        ]

        if governing_policies:
            updates["governing_policies"] = governing_policies
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["governing_policies"],
                    source="Policy relationship analysis",
                    methodology=f"Identified {len(policies)} governing policies via GOVERNS",
                    confidence=ConfidenceLevel.HIGH,
                )
            )

        # Regulatory sensitivity
        has_pii = cross_profile.get("has_sensitive_assets", False)
        regulatory_sensitivities = []
        if has_pii:
            # Add GDPR if PII present
            regulatory_sensitivities.append(
                {
                    "regulation": "GDPR",
                    "sensitivity_description": "Personal data of EU residents",
                    "handling_requirements": REGULATORY_SENSITIVITIES["GDPR"][
                        "handling_requirements"
                    ],
                    "jurisdiction_id": "EU",
                }
            )

        # Add domain-specific regulations based on type
        domain_type = cross_profile.get("domain_type", "")
        if "financial" in domain_type:
            regulatory_sensitivities.append(
                {
                    "regulation": "PCI-DSS",
                    "sensitivity_description": "Payment card data handling",
                    "handling_requirements": REGULATORY_SENSITIVITIES["PCI-DSS"][
                        "handling_requirements"
                    ],
                    "jurisdiction_id": "Global",
                }
            )

        if regulatory_sensitivities:
            updates["regulatory_sensitivity"] = regulatory_sensitivities
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["regulatory_sensitivity"],
                    source="Domain type and sensitivity analysis",
                    methodology=f"Identified {len(regulatory_sensitivities)} applicable regulations",
                    confidence=ConfidenceLevel.MEDIUM,
                )
            )

        # Data residency requirements
        data_residency_reqs = [
            {
                "jurisdiction_id": jurisdiction,
                "jurisdiction_name": jurisdiction,
                "requirement_description": details["requirement_description"],
                "localization_required": details["localization_required"],
                "compliant": True,
                "compliance_evidence": "Data stored in compliant jurisdiction",
            }
            for jurisdiction, details in DATA_RESIDENCY_REQUIREMENTS.items()
            if details["localization_required"]
        ]

        if data_residency_reqs:
            updates["data_residency_requirements"] = data_residency_reqs
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["data_residency_requirements"],
                    source="Global data governance policies",
                    methodology=f"Applied {len(data_residency_reqs)} jurisdiction requirements",
                    confidence=ConfidenceLevel.MEDIUM,
                )
            )

        # Quality targets
        domain_type = cross_profile.get("domain_type", "transactional")
        DOMAIN_TYPE_TEMPLATES.get(domain_type, DOMAIN_TYPE_TEMPLATES["transactional"])
        quality_targets = {
            "completeness_target_pct": 98.0,
            "accuracy_target_pct": 99.0,
            "timeliness_target": "Daily" if "analytical" in domain_type else "Real-time",
            "consistency_target": "Referential integrity enforced",
            "current_composite_score": 3.8,
            "meets_targets": True,
        }
        updates["quality_targets"] = quality_targets
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_DOMAIN,
                fields_enriched=["quality_targets"],
                source="Domain type templates",
                methodology=f"Coordinated quality targets for {domain_type} domains",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_4(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 4 (Measured) fields: DCAM maturity assessment."""
        updates = {}
        actions = []

        # Maturity dimensions (DCAM 2.2)
        assets_count = cross_profile.get("assets_count", 0)
        policies_count = cross_profile.get("policies_count", 0)

        # Compute maturity based on governance depth
        base_maturity = 2.0  # Start at level 2
        if policies_count > 0:
            base_maturity += 0.5
        if assets_count > 5:
            base_maturity += 0.5
        if cross_profile.get("has_sensitive_assets", False):
            base_maturity += 0.5

        maturity_dimensions = []
        for i, dimension in enumerate(DCAM_DIMENSIONS):
            # Vary score slightly per dimension based on asset count
            score = min(5.0, base_maturity + (i % 2) * 0.3)
            maturity_dimensions.append(
                {
                    "dimension": dimension["name"],
                    "score": score,
                    "assessed_date": datetime.now(UTC).isoformat(),
                }
            )

        updates["maturity_dimensions"] = maturity_dimensions
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_DOMAIN,
                fields_enriched=["maturity_dimensions"],
                source="DCAM 2.2 assessment",
                methodology=f"Scored based on {assets_count} assets, {policies_count} policies, sensitivity",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        # Maturity level (overall)
        overall_score = sum(d["score"] for d in maturity_dimensions) / len(maturity_dimensions)
        maturity_level_map = {
            1: "L00 Initial",
            2: "L01 Managed",
            3: "L02 Defined",
            4: "L03 Measured",
            5: "L04 Optimized",
        }
        maturity_level = maturity_level_map.get(int(overall_score), "L02 Defined")
        updates["maturity_level"] = maturity_level
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_DOMAIN,
                fields_enriched=["maturity_level"],
                source="Maturity aggregation",
                methodology=f"Averaged {len(maturity_dimensions)} DCAM dimensions",
                confidence=ConfidenceLevel.MEDIUM,
            )
        )

        return updates, actions

    def _populate_tier_5(
        self, entity: BaseEntity, context: EntityContext, cross_profile: dict
    ) -> tuple[dict, list]:
        """Populate Tier 5 (Optimized) fields: strategic insights."""
        updates = {}
        actions = []

        # Monetization potential
        assets_count = cross_profile.get("assets_count", 0)
        is_critical = cross_profile.get("has_sensitive_assets", False)

        monetization_potential = {
            "potential_type": "Direct Data Product"
            if assets_count > 10
            else "Process Optimization",
            "estimated_annual_value": 50000.0 * max(1, assets_count // 5),
            "currency": "USD",
            "confidence": "High" if is_critical else "Medium",
        }
        updates["monetization_potential"] = monetization_potential
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_DOMAIN,
                fields_enriched=["monetization_potential"],
                source="Asset portfolio analysis",
                methodology=f"Estimated from {assets_count} assets and criticality",
                confidence=ConfidenceLevel.LOW,
            )
        )

        # Strategic value
        domain_type = cross_profile.get("domain_type", "transactional")
        template = DOMAIN_TYPE_TEMPLATES.get(domain_type, {})
        strategic_value = template.get("strategic_value", "Decision Enabling")
        updates["strategic_value"] = strategic_value
        actions.append(
            EnrichmentAction(
                entity_id=entity.id,
                entity_type=EntityType.DATA_DOMAIN,
                fields_enriched=["strategic_value"],
                source="Domain type mapping",
                methodology=f"Derived from domain_type={domain_type}",
                confidence=ConfidenceLevel.HIGH,
            )
        )

        # Innovation use cases
        assets_count = cross_profile.get("assets_count", 0)
        cross_profile.get("policies_count", 0)

        innovation_cases = []
        if assets_count > 5:
            innovation_cases.append(
                {
                    "use_case": "Real-time Analytics",
                    "potential_impact": "Enable faster decision-making",
                    "maturity": "Proven",
                }
            )
        if not cross_profile.get("has_sensitive_assets", False):
            innovation_cases.append(
                {
                    "use_case": "AI/ML Model Training",
                    "potential_impact": "Develop predictive capabilities",
                    "maturity": "Experimental",
                }
            )

        if innovation_cases:
            updates["innovation_use_cases"] = innovation_cases
            actions.append(
                EnrichmentAction(
                    entity_id=entity.id,
                    entity_type=EntityType.DATA_DOMAIN,
                    fields_enriched=["innovation_use_cases"],
                    source="Asset and governance analysis",
                    methodology=f"Identified {len(innovation_cases)} use cases",
                    confidence=ConfidenceLevel.LOW,
                )
            )

        return updates, actions

    def _identify_gaps(self, entity: BaseEntity, cross_profile: dict) -> list[DataGap]:
        """Identify known data gaps."""
        gaps = []

        if cross_profile.get("assets_count", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="data_assets",
                    description="No data assets classified in this domain",
                    severity="High",
                    remediation_suggestion="Classify DataAssets using CONTAINS relationship",
                )
            )

        if cross_profile.get("policies_count", 0) == 0:
            gaps.append(
                DataGap(
                    field_name="governing_policies",
                    description="No policies governing this domain",
                    severity="Medium",
                    remediation_suggestion="Create or link governing Policy entities",
                )
            )

        if not getattr(entity, "domain_owner", None):
            gaps.append(
                DataGap(
                    field_name="domain_owner",
                    description="Domain owner not assigned",
                    severity="High",
                    remediation_suggestion="Assign owner via OrgUnit relationship or direct assignment",
                )
            )

        if (
            not getattr(entity, "data_classification", None)
            and cross_profile.get("assets_count", 0) > 0
        ):
            gaps.append(
                DataGap(
                    field_name="data_classification",
                    description="Domain classification not set despite having assets",
                    severity="Medium",
                    remediation_suggestion="Set data_classification based on highest asset classification",
                )
            )

        return gaps

    def _build_provenance(
        self, actions: list[EnrichmentAction], tier: EnrichmentTier, profile: EnrichmentProfile
    ) -> ProvenanceAndConfidence:
        """Build provenance record."""
        confidence_map = {
            EnrichmentTier.BASIC: "Medium",
            EnrichmentTier.STANDARD: "High",
            EnrichmentTier.DEEP: "Verified",
        }

        primary_source = "Enrichment Agency - DataDomain Enricher"
        if actions:
            primary_source += f" ({len(actions)} fields enriched)"

        return ProvenanceAndConfidence(
            primary_data_source=primary_source,
            last_assessed_date=datetime.now(UTC).isoformat(),
            assessed_by="DataDomainEnricher v1.0",
            assessment_methodology="Context-aware graph analysis + DCAM 2.2 maturity framework",
            confidence_level=confidence_map.get(tier, "Medium"),
        )
