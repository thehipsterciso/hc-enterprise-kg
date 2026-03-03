"""Provenance & Confidence Reconciler for the Knowledge Graph Enrichment Agency.

This module provides the provenance tracking heart of the enrichment agency.
Every enrichment action must update provenance and confidence, and these must
be reconsidered as enrichment deepens.

The ProvenanceReconciler class:
- Records enrichment actions with source, methodology, and confidence
- Recalculates entity confidence considering source quality, data freshness,
  completeness, and neighbor consistency
- Adjusts relationship confidence based on entity confidences
- Identifies data gaps for remediation
- Handles naming differences between entity types (provenance vs
  provenance_and_confidence)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from domain.base import BaseEntity, EntityType
from domain.shared import DataGap, DataQualityScore, ProvenanceAndConfidence
from enrichment.base import (
    AssessmentMethodology,
    ConfidenceLevel,
    CONFIDENCE_RUBRIC,
    EnrichmentAction,
    FieldCategory,
    SOURCE_VALIDITY_WINDOWS,
)

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph


# Mapping of entity types that use "provenance_and_confidence" vs "provenance"
PROVENANCE_AND_CONFIDENCE_ENTITIES = {
    EntityType.INITIATIVE,
    EntityType.VENDOR,
    EntityType.CONTRACT,
    EntityType.CUSTOMER,
    EntityType.PRODUCT,
    EntityType.PRODUCT_PORTFOLIO,
    EntityType.MARKET_SEGMENT,
}


class ProvenanceReconciler:
    """Reconciles provenance and confidence across enrichment actions.

    Maintains audit trails of enrichment actions and recalculates confidence
    levels based on source quality, data freshness, completeness, and
    cross-entity consistency.
    """

    # Version for assessed_by tracking
    ENRICHMENT_AGENCY_VERSION = "0.35.0"

    def __init__(self, kg: KnowledgeGraph | None = None):
        """Initialize the reconciler with optional knowledge graph reference.

        Args:
            kg: Optional KnowledgeGraph instance for neighbor consistency checks.
        """
        self.kg = kg
        # Enrichment action log per entity for audit trail
        self.enrichment_log: dict[str, list[EnrichmentAction]] = {}

    def record_enrichment(
        self,
        entity_id: str,
        entity_type: EntityType,
        fields_enriched: list[str],
        source: str,
        methodology: AssessmentMethodology | str,
        confidence: ConfidenceLevel | str,
        source_date: str | None = None,
    ) -> ProvenanceAndConfidence:
        """Record enrichment for a batch of field updates.

        Updates the entity's provenance fields including:
        - primary_data_source (specific source, not generic category)
        - assessed_by (EnrichmentAgency/{enricher_name}/v0.35.0)
        - assessment_methodology (Automated | Hybrid | Manual | Import)
        - confidence_level (Verified | High | Medium | Low | Unverified)
        - last_assessed_date (ISO format)
        - data_quality_score (recalculated based on completeness)

        Source staleness enforcement: if source_date is provided, the confidence
        level is capped by the SOURCE_VALIDITY_WINDOWS for the source type.
        A SOC 2 report from 2023 cannot support VERIFIED confidence in 2026.

        Args:
            entity_id: ID of the entity being enriched.
            entity_type: Type of the entity.
            fields_enriched: List of field names that were enriched.
            source: Specific source of the enriched data (e.g., "NIST SP 800-53 Rev 5",
                    not just "NIST"). Must be attributable.
            methodology: Assessment methodology enum or string.
            confidence: Confidence level for the enrichment.
            source_date: ISO date when the source data was published/retrieved.

        Returns:
            Updated ProvenanceAndConfidence record.
        """
        # Normalize confidence level
        if isinstance(confidence, str):
            try:
                confidence = ConfidenceLevel(confidence.lower())
            except ValueError:
                confidence = ConfidenceLevel.UNVERIFIED

        # Normalize methodology to AssessmentMethodology enum
        if isinstance(methodology, str):
            try:
                methodology = AssessmentMethodology(methodology.lower())
            except ValueError:
                methodology = AssessmentMethodology.HYBRID

        # Apply source staleness cap
        validity_window = self._get_validity_window(source)
        if source_date and validity_window > 0:
            confidence = self._apply_staleness_cap(confidence, source_date, validity_window)

        # Record the action in audit log
        action = EnrichmentAction(
            entity_id=entity_id,
            entity_type=entity_type,
            fields_enriched=fields_enriched,
            source=source,
            methodology=methodology,
            confidence=confidence,
            source_date=source_date,
            validity_window_days=validity_window,
        )
        if entity_id not in self.enrichment_log:
            self.enrichment_log[entity_id] = []
        self.enrichment_log[entity_id].append(action)

        # Build provenance record
        provenance = ProvenanceAndConfidence(
            primary_data_source=source,
            assessed_by=f"EnrichmentAgency/enricher/v{self.ENRICHMENT_AGENCY_VERSION}",
            assessment_methodology=methodology.value if isinstance(methodology, AssessmentMethodology) else methodology,
            confidence_level=confidence.value,
            last_assessed_date=datetime.now(UTC).isoformat(),
        )

        return provenance

    def _get_validity_window(self, source: str) -> int:
        """Determine the validity window for a source based on its type.

        Matches source string against known source type patterns in
        SOURCE_VALIDITY_WINDOWS.

        Args:
            source: The source string (e.g., "NIST SP 800-53 Rev 5").

        Returns:
            Validity window in days, or 365 as default.
        """
        source_lower = source.lower()
        for source_type, days in SOURCE_VALIDITY_WINDOWS.items():
            if source_type in source_lower:
                return days
        # Default validity window
        return 365

    def _apply_staleness_cap(
        self,
        confidence: ConfidenceLevel,
        source_date: str,
        validity_window: int,
    ) -> ConfidenceLevel:
        """Cap confidence based on source staleness.

        If the source data is older than its validity window, the confidence
        is downgraded appropriately.

        Args:
            confidence: The claimed confidence level.
            source_date: ISO date when source data was published/retrieved.
            validity_window: How many days this source type remains valid.

        Returns:
            Potentially downgraded ConfidenceLevel.
        """
        try:
            dt = datetime.fromisoformat(source_date.replace("Z", "+00:00"))
            days_old = (datetime.now(UTC) - dt).days

            if days_old <= validity_window:
                return confidence  # Source is fresh

            # Staleness-based downgrade ladder
            staleness_ratio = days_old / max(validity_window, 1)

            if staleness_ratio > 3.0:
                return ConfidenceLevel.UNVERIFIED
            elif staleness_ratio > 2.0:
                return ConfidenceLevel.LOW
            elif staleness_ratio > 1.0:
                # One step down from claimed
                levels = list(ConfidenceLevel)
                current_idx = levels.index(confidence)
                return levels[min(current_idx + 1, len(levels) - 1)]

        except (ValueError, TypeError):
            pass  # Can't parse date — return as-is

        return confidence

    def recalculate_entity_confidence(
        self,
        entity: BaseEntity,
        tier_fields: list[str] | None = None,
        field_categories: dict[str, FieldCategory] | None = None,
    ) -> ProvenanceAndConfidence:
        """Recalculate overall entity confidence using the 4-factor model.

        Factors (each scored 0.0-1.0, weighted):
        1. Source quality (weight 0.35) — average confidence from enrichment actions
        2. Timeliness (weight 0.25) — are sources within their validity windows?
        3. Completeness (weight 0.25) — weighted by field category (critical 3x, operational 2x, metadata 1x)
        4. Consistency (weight 0.15) — cross-entity coherence with neighbors

        Confidence ceiling rules (hard caps that override the weighted score):
        - Critical field completeness < 50%: max MEDIUM regardless of other factors
        - Critical field completeness < 25%: max LOW regardless of other factors
        - No enrichment actions logged: max LOW (no provenance trail)
        - All sources stale: max LOW (no fresh evidence)

        Args:
            entity: The entity to recalculate confidence for.
            tier_fields: Expected fields for the entity's tier (for completeness).
            field_categories: Mapping of field_name → FieldCategory for weighted scoring.

        Returns:
            Recalculated ProvenanceAndConfidence record.
        """
        provenance_field_name = self.get_provenance_field_name(entity.entity_type)
        existing_provenance: ProvenanceAndConfidence = getattr(
            entity, provenance_field_name, ProvenanceAndConfidence()
        )

        # --- Factor 1: Source quality (0.0-1.0) ---
        source_quality = 0.2  # Default to UNVERIFIED level
        confidence_scores = {
            ConfidenceLevel.VERIFIED: 1.0,
            ConfidenceLevel.HIGH: 0.85,
            ConfidenceLevel.MEDIUM: 0.65,
            ConfidenceLevel.LOW: 0.4,
            ConfidenceLevel.UNVERIFIED: 0.2,
        }

        has_actions = entity.id in self.enrichment_log and self.enrichment_log[entity.id]
        if has_actions:
            actions = self.enrichment_log[entity.id]
            source_quality = sum(
                confidence_scores.get(
                    ConfidenceLevel(action.confidence.lower())
                    if isinstance(action.confidence, str)
                    else action.confidence,
                    0.2,
                )
                for action in actions
            ) / len(actions)

        # --- Factor 2: Timeliness (0.0-1.0) ---
        timeliness_score_str = "Outdated"
        timeliness_numeric = 0.0

        if has_actions:
            actions = self.enrichment_log[entity.id]
            fresh_count = 0
            stale_count = 0
            for action in actions:
                if action.source_date:
                    try:
                        src_dt = datetime.fromisoformat(
                            action.source_date.replace("Z", "+00:00")
                        )
                        days_old = (datetime.now(UTC) - src_dt).days
                        validity = action.validity_window_days or 365
                        if days_old <= validity:
                            fresh_count += 1
                        else:
                            stale_count += 1
                    except (ValueError, TypeError):
                        stale_count += 1
                else:
                    # No source date — treat as stale
                    stale_count += 1

            total = fresh_count + stale_count
            if total > 0:
                timeliness_numeric = fresh_count / total
        elif existing_provenance.last_assessed_date:
            try:
                assessed_date = datetime.fromisoformat(
                    existing_provenance.last_assessed_date.replace("Z", "+00:00")
                )
                days_since = (datetime.now(UTC) - assessed_date).days
                if days_since < 30:
                    timeliness_numeric = 1.0
                elif days_since < 90:
                    timeliness_numeric = 0.75
                elif days_since < 365:
                    timeliness_numeric = 0.4
                else:
                    timeliness_numeric = 0.1
            except (ValueError, AttributeError):
                timeliness_numeric = 0.0

        # Map numeric timeliness to human-readable
        if timeliness_numeric >= 0.8:
            timeliness_score_str = "Current"
        elif timeliness_numeric >= 0.5:
            timeliness_score_str = "Recent"
        elif timeliness_numeric >= 0.2:
            timeliness_score_str = "Stale"
        else:
            timeliness_score_str = "Outdated"

        # --- Factor 3: Completeness (weighted by field category) ---
        completeness_pct = 0.0
        critical_completeness = 1.0  # Default to full if no categories provided

        if tier_fields:
            if field_categories:
                completeness_pct = self._weighted_completeness(
                    entity, tier_fields, field_categories
                )
                critical_completeness = self._category_completeness(
                    entity, tier_fields, field_categories, FieldCategory.CRITICAL
                )
            else:
                completeness_pct = self.calculate_completeness(entity, tier_fields)
                critical_completeness = completeness_pct  # Without categories, use overall

        # --- Factor 4: Consistency with neighbors ---
        consistency_score_str = "Not Assessed"
        consistency_numeric = 0.5  # Neutral default

        if self.kg:
            consistency_score_str = self._assess_neighbor_consistency(entity)
            consistency_map = {
                "Consistent": 1.0,
                "Minor Inconsistencies": 0.7,
                "Major Inconsistencies": 0.3,
                "Not Assessed": 0.5,
            }
            consistency_numeric = consistency_map.get(consistency_score_str, 0.5)

        # --- Weighted composite score ---
        composite = (
            source_quality * 0.35
            + timeliness_numeric * 0.25
            + completeness_pct * 0.25
            + consistency_numeric * 0.15
        )

        # Map composite to confidence level
        if composite >= 0.85:
            final_confidence = ConfidenceLevel.VERIFIED
        elif composite >= 0.70:
            final_confidence = ConfidenceLevel.HIGH
        elif composite >= 0.50:
            final_confidence = ConfidenceLevel.MEDIUM
        elif composite >= 0.30:
            final_confidence = ConfidenceLevel.LOW
        else:
            final_confidence = ConfidenceLevel.UNVERIFIED

        # --- Apply hard confidence ceilings ---
        if not has_actions:
            # No enrichment trail — can't exceed LOW
            if final_confidence in (ConfidenceLevel.VERIFIED, ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
                final_confidence = ConfidenceLevel.LOW

        if critical_completeness < 0.25:
            if final_confidence in (ConfidenceLevel.VERIFIED, ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
                final_confidence = ConfidenceLevel.LOW
        elif critical_completeness < 0.50:
            if final_confidence in (ConfidenceLevel.VERIFIED, ConfidenceLevel.HIGH):
                final_confidence = ConfidenceLevel.MEDIUM

        if timeliness_numeric == 0.0:
            # All sources stale — can't exceed LOW
            if final_confidence in (ConfidenceLevel.VERIFIED, ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
                final_confidence = ConfidenceLevel.LOW

        # Build data quality score
        data_quality = DataQualityScore(
            completeness_pct=completeness_pct * 100 if completeness_pct else None,
            accuracy_confidence=final_confidence.value.capitalize(),
            timeliness_score=timeliness_score_str,
            consistency_score=consistency_score_str,
        )

        # Return updated provenance
        return ProvenanceAndConfidence(
            data_quality_score=data_quality,
            primary_data_source=existing_provenance.primary_data_source,
            last_assessed_date=datetime.now(UTC).isoformat(),
            assessed_by=existing_provenance.assessed_by
            or f"EnrichmentAgency/reconciler/v{self.ENRICHMENT_AGENCY_VERSION}",
            assessment_methodology=existing_provenance.assessment_methodology
            or AssessmentMethodology.HYBRID.value,
            confidence_level=final_confidence.value,
            attestation_status=existing_provenance.attestation_status,
            known_data_gaps=existing_provenance.known_data_gaps,
        )

    def _weighted_completeness(
        self,
        entity: BaseEntity,
        tier_fields: list[str],
        field_categories: dict[str, FieldCategory],
    ) -> float:
        """Calculate weighted completeness using field category weights.

        Critical fields weight 3x, operational 2x, metadata 1x.
        """
        category_weights = {
            FieldCategory.CRITICAL: 3.0,
            FieldCategory.OPERATIONAL: 2.0,
            FieldCategory.METADATA: 1.0,
        }
        total_weight = 0.0
        populated_weight = 0.0

        for field_name in tier_fields:
            category = field_categories.get(field_name, FieldCategory.METADATA)
            weight = category_weights[category]
            total_weight += weight

            value = getattr(entity, field_name, None)
            if value is not None and value != "" and value != []:
                populated_weight += weight

        return populated_weight / total_weight if total_weight > 0 else 0.0

    def _category_completeness(
        self,
        entity: BaseEntity,
        tier_fields: list[str],
        field_categories: dict[str, FieldCategory],
        target_category: FieldCategory,
    ) -> float:
        """Calculate completeness for a specific field category only."""
        total = 0
        populated = 0

        for field_name in tier_fields:
            category = field_categories.get(field_name, FieldCategory.METADATA)
            if category != target_category:
                continue
            total += 1
            value = getattr(entity, field_name, None)
            if value is not None and value != "" and value != []:
                populated += 1

        return populated / total if total > 0 else 1.0  # Default to 1.0 if no critical fields

    def recalculate_relationship_confidence(
        self, source_entity: BaseEntity, target_entity: BaseEntity
    ) -> float:
        """Adjust relationship confidence based on entity confidences.

        Relationship confidence = min(
            source_entity_confidence_numeric,
            target_entity_confidence_numeric,
            edge_evidence_quality
        )

        Where confidence_numeric maps:
        - Verified = 1.0
        - High = 0.85
        - Medium = 0.65
        - Low = 0.4
        - Unverified = 0.2

        Args:
            source_entity: Source entity of the relationship.
            target_entity: Target entity of the relationship.

        Returns:
            Numeric confidence score (0.0-1.0).
        """
        confidence_numeric_map = {
            "verified": 1.0,
            "high": 0.85,
            "medium": 0.65,
            "low": 0.4,
            "unverified": 0.2,
        }

        # Extract confidence levels from entities
        source_field = self.get_provenance_field_name(source_entity.entity_type)
        source_prov: ProvenanceAndConfidence = getattr(
            source_entity, source_field, ProvenanceAndConfidence()
        )
        source_confidence = confidence_numeric_map.get(
            source_prov.confidence_level.lower() if source_prov.confidence_level else "",
            0.65,
        )

        target_field = self.get_provenance_field_name(target_entity.entity_type)
        target_prov: ProvenanceAndConfidence = getattr(
            target_entity, target_field, ProvenanceAndConfidence()
        )
        target_confidence = confidence_numeric_map.get(
            target_prov.confidence_level.lower() if target_prov.confidence_level else "",
            0.65,
        )

        # Default edge evidence quality (could be enhanced with actual edge metadata)
        edge_evidence_quality = 0.75

        # Return minimum of the three factors
        return min(source_confidence, target_confidence, edge_evidence_quality)

    def calculate_completeness(self, entity: BaseEntity, tier_fields: list[str]) -> float:
        """Calculate what percentage of tier-expected fields are populated.

        A field is considered populated if it is:
        - Not None
        - Not empty string
        - Not empty list

        Args:
            entity: The entity to assess.
            tier_fields: Expected field names for the tier.

        Returns:
            Completeness percentage (0.0-1.0).
        """
        if not tier_fields:
            return 0.0

        populated_count = 0
        for field_name in tier_fields:
            value = getattr(entity, field_name, None)
            # Check if field is populated (non-empty)
            if value is not None and value != "" and value != []:
                populated_count += 1

        return populated_count / len(tier_fields)

    def identify_data_gaps(
        self, entity: BaseEntity, tier_fields: list[str]
    ) -> list[DataGap]:
        """Identify unfilled fields at the current tier with remediation suggestions.

        Returns DataGap entries for all unfilled fields, including priority
        and suggested remediation approach.

        Args:
            entity: The entity to assess for gaps.
            tier_fields: Expected field names for the tier.

        Returns:
            List of DataGap records.
        """
        gaps = []

        for field_name in tier_fields:
            value = getattr(entity, field_name, None)
            # Check if field is unpopulated
            if value is None or value == "" or value == []:
                # Infer priority based on field name patterns
                priority = self._infer_gap_priority(field_name, entity.entity_type)

                # Suggest remediation approach
                remediation = self._suggest_remediation(field_name, entity.entity_type)

                gap = DataGap(
                    attribute_name=field_name,
                    gap_description=f"Field '{field_name}' is not populated for {entity.entity_type}",
                    remediation_plan=remediation,
                    priority=priority,
                )
                gaps.append(gap)

        return gaps

    def get_provenance_field_name(self, entity_type: EntityType) -> str:
        """Return the provenance field name for an entity type.

        Initiative, Vendor, Contract, Customer, Product, ProductPortfolio,
        MarketSegment use "provenance_and_confidence".
        All others use "provenance".

        Args:
            entity_type: The entity type to check.

        Returns:
            Field name: "provenance_and_confidence" or "provenance".
        """
        if entity_type in PROVENANCE_AND_CONFIDENCE_ENTITIES:
            return "provenance_and_confidence"
        return "provenance"

    # ========================================================================
    # Private helpers
    # ========================================================================

    def _assess_neighbor_consistency(self, entity: BaseEntity) -> str:
        """Assess consistency of entity data with neighbor data.

        This is a placeholder for cross-entity consistency checks that can
        be performed if the knowledge graph is available.

        Args:
            entity: The entity to assess.

        Returns:
            Consistency score string: "Consistent", "Minor Inconsistencies",
            "Major Inconsistencies", or "Not Assessed".
        """
        if not self.kg:
            return "Not Assessed"

        # Placeholder implementation
        # In a full implementation, this would check things like:
        # - Role entity consistency with Person role assignments
        # - Department head consistency across org structure
        # - Relationship reciprocity (if A manages B, B reports to A)
        # - Data type compatibility across linked entities

        return "Not Assessed"

    def _infer_gap_priority(self, field_name: str, entity_type: EntityType) -> str:
        """Infer remediation priority based on field naming and context.

        Args:
            field_name: The field name with missing data.
            entity_type: Type of entity.

        Returns:
            Priority string: "Critical", "High", "Medium", or "Low".
        """
        # Critical fields (key identity, compliance, risk)
        critical_patterns = [
            "name",
            "status",
            "risk",
            "compliance",
            "confidentiality",
            "integrity",
            "availability",
            "owner",
            "responsible",
        ]

        # High priority (operational relevance)
        high_patterns = [
            "description",
            "location",
            "contact",
            "relationship",
            "dependency",
            "classification",
            "assessment",
        ]

        field_lower = field_name.lower()

        for pattern in critical_patterns:
            if pattern in field_lower:
                return "Critical"

        for pattern in high_patterns:
            if pattern in field_lower:
                return "High"

        # Medium for most other populated fields
        if any(
            x in field_lower for x in ["date", "score", "count", "metric", "rate"]
        ):
            return "Medium"

        return "Low"

    def _suggest_remediation(self, field_name: str, entity_type: EntityType) -> str:
        """Suggest remediation approach for a data gap.

        Args:
            field_name: The field name with missing data.
            entity_type: Type of entity.

        Returns:
            Remediation suggestion string.
        """
        field_lower = field_name.lower()

        # Map field patterns to remediation strategies
        if any(x in field_lower for x in ["description", "details", "comment"]):
            return "Review related entities and OSINT data; conduct manual research"

        if any(x in field_lower for x in ["date", "timestamp"]):
            return "Check audit logs or system records for temporal data"

        if any(
            x in field_lower for x in ["location", "address", "geography", "site"]
        ):
            return "Cross-reference with Location/Geography entities or external data"

        if any(
            x in field_lower for x in ["relationship", "dependency", "manages", "role"]
        ):
            return "Analyze graph neighborhood; infer from related entities"

        if any(
            x in field_lower for x in ["risk", "assessment", "compliance", "status"]
        ):
            return "Conduct risk assessment; consult with domain experts"

        if any(x in field_lower for x in ["contact", "owner", "manager", "sponsor"]):
            return "Query organizational data; conduct stakeholder interviews"

        if any(
            x in field_lower for x in ["financial", "budget", "cost", "spend", "revenue"]
        ):
            return "Consult financial systems and accounting records"

        return "Conduct targeted enrichment and validation with subject matter experts"
