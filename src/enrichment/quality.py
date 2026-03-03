"""EnrichmentQualityReport — assess enrichment quality against tier expectations.

Evaluates:
- Field population by tier (what % of expected fields are populated)
- Cross-entity coherence (do relationships link enriched fields)
- Temporal consistency (dates in proper order)
- Framework mapping completeness (control → regulation mappings)
- Provenance coverage (% of entities have provenance set)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from domain.base import EntityType
from enrichment.base import FieldCategory
from enrichment.tier_definitions import TIER_FIELDS

if TYPE_CHECKING:
    from graph.knowledge_graph import KnowledgeGraph


@dataclass
class FieldPopulationDetail:
    """Detailed field population breakdown for a single tier."""

    tier: int
    total_fields: int = 0
    populated_fields: int = 0
    unweighted_pct: float = 0.0
    weighted_pct: float = (
        0.0  # Weighted by FieldCategory (critical 3x, operational 2x, metadata 1x)
    )
    critical_pct: float = 0.0  # Critical fields only
    operational_pct: float = 0.0  # Operational fields only
    metadata_pct: float = 0.0  # Metadata fields only
    missing_critical: list[str] = field(default_factory=list)


@dataclass
class EnrichmentQualityReport:
    """Results of a quality assessment on enriched data.

    Reports both unweighted and weighted completeness, broken down by
    field category (critical/operational/metadata) so that decision-makers
    can assess whether the enrichment is operationally trustworthy, not just
    numerically complete.
    """

    overall_score: float = 0.0
    field_population_by_tier: dict[int, float] = field(
        default_factory=dict
    )  # tier → unweighted population %
    weighted_population_by_tier: dict[int, float] = field(
        default_factory=dict
    )  # tier → weighted population %
    field_population_detail: list[FieldPopulationDetail] = field(default_factory=list)
    cross_entity_coherence: float = 0.0
    temporal_consistency: float = 0.0
    framework_mapping_completeness: float = 0.0
    provenance_coverage: float = 0.0  # % of entities with provenance set
    adversarial_rejection_rate: float = 0.0  # % of field updates rejected by validator
    enrichment_recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary of the enrichment quality report."""
        lines = [
            f"Enrichment Quality Score: {self.overall_score:.2f}",
            "  Field Population (by tier):",
        ]
        for detail in self.field_population_detail:
            lines.append(f"    Tier {detail.tier}:")
            lines.append(
                f"      Unweighted: {detail.unweighted_pct:.1%} ({detail.populated_fields}/{detail.total_fields})"
            )
            lines.append(f"      Weighted:   {detail.weighted_pct:.1%}")
            lines.append(f"      Critical:   {detail.critical_pct:.1%}")
            lines.append(f"      Operational: {detail.operational_pct:.1%}")
            lines.append(f"      Metadata:   {detail.metadata_pct:.1%}")
            if detail.missing_critical:
                lines.append(
                    f"      Missing Critical Fields: {', '.join(detail.missing_critical[:5])}"
                )

        # Fallback for old-style tier data
        if not self.field_population_detail:
            for tier in sorted(self.field_population_by_tier.keys()):
                pct = self.field_population_by_tier[tier]
                lines.append(f"    Tier {tier}: {pct:.1%}")

        lines.extend(
            [
                f"  Cross-Entity Coherence:        {self.cross_entity_coherence:.2f}",
                f"  Temporal Consistency:          {self.temporal_consistency:.2f}",
                f"  Framework Mapping Completeness: {self.framework_mapping_completeness:.2f}",
                f"  Provenance Coverage:           {self.provenance_coverage:.1%}",
                f"  Adversarial Rejection Rate:    {self.adversarial_rejection_rate:.1%}",
            ]
        )

        if self.enrichment_recommendations:
            lines.append(f"  Recommendations: {len(self.enrichment_recommendations)}")
            for rec in self.enrichment_recommendations[:5]:
                lines.append(f"    - {rec}")

        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings[:3]:
                lines.append(f"    - {w}")

        return "\n".join(lines)


def assess_enrichment_quality(kg: KnowledgeGraph, tier: int) -> EnrichmentQualityReport:
    """Assess enrichment quality of the knowledge graph at a given tier.

    Args:
        kg: The knowledge graph to assess.
        tier: The enrichment tier (1-5) to assess against.

    Returns:
        EnrichmentQualityReport with scores and recommendations.
    """
    report = EnrichmentQualityReport()
    scores = []

    # 1. Field population: what % of expected fields are populated per tier
    pop_score = _check_field_population(kg, tier, report)
    scores.append(pop_score)

    # 2. Cross-entity coherence: relationships link enriched fields
    coherence_score = _check_cross_entity_coherence(kg, report)
    scores.append(coherence_score)

    # 3. Temporal consistency: dates in proper order
    temporal_score = _check_temporal_consistency(kg, report)
    scores.append(temporal_score)

    # 4. Framework mapping completeness: controls have regulation mappings
    framework_score = _check_framework_mapping(kg, report)
    scores.append(framework_score)

    # 5. Provenance coverage: % with non-empty provenance
    prov_score = _check_provenance_coverage(kg, report)
    scores.append(prov_score)

    # Compute overall score
    if scores:
        report.overall_score = sum(scores) / len(scores)
    else:
        report.overall_score = 0.0

    return report


def _check_field_population(
    kg: KnowledgeGraph, tier: int, report: EnrichmentQualityReport
) -> float:
    """Check what percentage of expected fields are populated at each tier.

    Computes both unweighted and weighted completeness. Weighted completeness
    uses FieldCategory weights: critical (3x), operational (2x), metadata (1x).

    Maps entity types to expected fields from TIER_FIELDS, counts non-None/non-empty,
    and computes population % per tier with category breakdown.
    """
    tier_population = {}
    weighted_population = {}
    category_weights = {
        FieldCategory.CRITICAL: 3.0,
        FieldCategory.OPERATIONAL: 2.0,
        FieldCategory.METADATA: 1.0,
    }

    # For each tier from 2 to target tier
    for check_tier in range(2, tier + 1):
        total_expected = 0
        total_populated = 0
        total_weight = 0.0
        populated_weight = 0.0
        critical_total = 0
        critical_populated = 0
        operational_total = 0
        operational_populated = 0
        metadata_total = 0
        metadata_populated = 0
        missing_critical_fields: list[str] = []

        # Iterate entities and check field population
        for entity_type in EntityType:
            type_str = entity_type.value
            if type_str not in TIER_FIELDS:
                continue

            tier_fields_dict = TIER_FIELDS[type_str]
            if check_tier not in tier_fields_dict:
                continue

            expected_fields = tier_fields_dict[check_tier]
            entities = kg.list_entities(entity_type)

            for entity in entities:
                for field_name in expected_fields:
                    total_expected += 1

                    # Determine field category
                    category = _classify_field(field_name, entity_type)
                    weight = category_weights[category]
                    total_weight += weight

                    if category == FieldCategory.CRITICAL:
                        critical_total += 1
                    elif category == FieldCategory.OPERATIONAL:
                        operational_total += 1
                    else:
                        metadata_total += 1

                    try:
                        val = getattr(entity, field_name, None)
                        if val is not None and val != "" and val != []:
                            total_populated += 1
                            populated_weight += weight
                            if category == FieldCategory.CRITICAL:
                                critical_populated += 1
                            elif category == FieldCategory.OPERATIONAL:
                                operational_populated += 1
                            else:
                                metadata_populated += 1
                        elif category == FieldCategory.CRITICAL:
                            missing_critical_fields.append(f"{type_str}.{field_name}")
                    except (AttributeError, KeyError):
                        if category == FieldCategory.CRITICAL:
                            missing_critical_fields.append(f"{type_str}.{field_name}")

        # Unweighted
        unweighted_pct = total_populated / total_expected if total_expected > 0 else 0.0
        tier_population[check_tier] = unweighted_pct

        # Weighted
        weighted_pct = populated_weight / total_weight if total_weight > 0 else 0.0
        weighted_population[check_tier] = weighted_pct

        # Category breakdowns
        crit_pct = critical_populated / critical_total if critical_total > 0 else 1.0
        oper_pct = operational_populated / operational_total if operational_total > 0 else 1.0
        meta_pct = metadata_populated / metadata_total if metadata_total > 0 else 1.0

        detail = FieldPopulationDetail(
            tier=check_tier,
            total_fields=total_expected,
            populated_fields=total_populated,
            unweighted_pct=unweighted_pct,
            weighted_pct=weighted_pct,
            critical_pct=crit_pct,
            operational_pct=oper_pct,
            metadata_pct=meta_pct,
            missing_critical=missing_critical_fields[:20],  # Cap at 20 for readability
        )
        report.field_population_detail.append(detail)

    report.field_population_by_tier = tier_population
    report.weighted_population_by_tier = weighted_population

    # Overall score uses weighted completeness
    if weighted_population:
        pop_score = sum(weighted_population.values()) / len(weighted_population)
    else:
        pop_score = 0.0

    if pop_score < 0.5:
        report.warnings.append(f"Low weighted field population at tier {tier}: {pop_score:.1%}")
    if pop_score < 0.3:
        report.enrichment_recommendations.append(
            "Weighted field population is very low; critical fields are under-enriched"
        )

    # Warn specifically about critical field gaps
    for detail in report.field_population_detail:
        if detail.critical_pct < 0.5:
            report.warnings.append(
                f"Tier {detail.tier}: Only {detail.critical_pct:.0%} of critical fields populated"
            )

    return pop_score


def _classify_field(field_name: str, entity_type: EntityType) -> FieldCategory:
    """Classify a field into critical/operational/metadata based on naming patterns.

    Critical fields: identity, ownership, risk/compliance, classification, status.
    These are load-bearing for operational decisions.

    Operational fields: descriptions, locations, contacts, dates, assessments.
    These inform day-to-day operations.

    Metadata fields: provenance, audit trails, tags, notes, versioning.
    These track process but don't drive decisions.
    """
    fn = field_name.lower()

    # Critical patterns — load-bearing for risk, compliance, and operations
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
        "classification",
        "criticality",
        "severity",
        "control_type",
        "threat_level",
        "risk_level",
        "encryption",
        "regulation",
        "jurisdiction",
        "effective_date",
        "entity_type",
    ]

    # Operational patterns — day-to-day business operations
    operational_patterns = [
        "description",
        "location",
        "contact",
        "email",
        "phone",
        "address",
        "department",
        "role",
        "budget",
        "cost",
        "value",
        "count",
        "score",
        "frequency",
        "assessment",
        "remediation",
        "implementation",
        "capability",
        "requirement",
        "dependency",
        "integration",
    ]

    # Metadata patterns — process tracking and audit
    metadata_patterns = [
        "provenance",
        "temporal",
        "created_at",
        "updated_at",
        "version",
        "tag",
        "note",
        "comment",
        "audit",
        "log",
        "history",
        "attestation",
        "data_quality",
        "assessed_by",
        "methodology",
        "confidence",
        "last_assessed",
        "valid_from",
        "valid_until",
    ]

    for pattern in critical_patterns:
        if pattern in fn:
            return FieldCategory.CRITICAL

    for pattern in metadata_patterns:
        if pattern in fn:
            return FieldCategory.METADATA

    for pattern in operational_patterns:
        if pattern in fn:
            return FieldCategory.OPERATIONAL

    return FieldCategory.OPERATIONAL  # Default to operational


def _check_cross_entity_coherence(kg: KnowledgeGraph, report: EnrichmentQualityReport) -> float:
    """Check coherence: do relationships link to enriched entities?

    For a sample of relationships, check that both endpoints are enriched
    (have non-identity fields populated).
    """
    rels = kg.list_relationships(limit=100)
    if not rels:
        return 1.0  # No relationships to check

    coherent_count = 0
    for rel in rels:
        try:
            source = kg.get_entity(rel.source_id)
            target = kg.get_entity(rel.target_id)
            if source and target:
                # Rough check: entity has fields beyond id/entity_type
                source_enriched = len([f for f in source.__dict__ if not f.startswith("_")]) > 3
                target_enriched = len([f for f in target.__dict__ if not f.startswith("_")]) > 3
                if source_enriched and target_enriched:
                    coherent_count += 1
        except (AttributeError, KeyError):
            pass

    score = coherent_count / len(rels) if rels else 0.0
    report.cross_entity_coherence = score

    if score < 0.6:
        report.warnings.append(
            "Cross-entity coherence is low; some relationships lack enriched endpoints"
        )

    return score


def _check_temporal_consistency(kg: KnowledgeGraph, report: EnrichmentQualityReport) -> float:
    """Check temporal consistency: dates are in proper order.

    Sample entities with date fields (created_at, updated_at) and verify ordering.
    """
    consistent_count = 0
    total_checked = 0

    for entity_type in EntityType:
        entities = kg.list_entities(entity_type, limit=20)
        for entity in entities:
            try:
                created = getattr(entity, "created_at", None)
                updated = getattr(entity, "updated_at", None)
                if created and updated:
                    total_checked += 1
                    if created <= updated:
                        consistent_count += 1
            except (AttributeError, TypeError):
                pass

    score = consistent_count / total_checked if total_checked > 0 else 1.0
    report.temporal_consistency = score

    if score < 0.9:
        report.warnings.append(
            "Some entities have temporal inconsistencies (created_at > updated_at)"
        )

    return score


def _check_framework_mapping(kg: KnowledgeGraph, report: EnrichmentQualityReport) -> float:
    """Check framework mapping completeness: controls → regulations.

    For a sample of controls, check they map to regulations via framework_mappings or relationships.
    """
    controls = kg.list_entities(EntityType.CONTROL, limit=50)
    if not controls:
        return 1.0

    mapped_count = 0
    for control in controls:
        try:
            # Check if control has framework_mappings or related regulations
            mappings = getattr(control, "framework_mappings", None)
            if mappings and len(mappings) > 0:
                mapped_count += 1
            else:
                # Check relationships to regulations
                neighbors = kg.engine.get_neighbors(control.id, relationship_type="subject_to")
                if neighbors:
                    mapped_count += 1
        except (AttributeError, KeyError):
            pass

    score = mapped_count / len(controls) if controls else 0.0
    report.framework_mapping_completeness = score

    if score < 0.7:
        report.enrichment_recommendations.append(
            "Consider enriching control framework_mappings for better regulatory traceability"
        )

    return score


def _check_provenance_coverage(kg: KnowledgeGraph, report: EnrichmentQualityReport) -> float:
    """Check provenance coverage: what % of entities have non-empty provenance?

    Provenance can be in 'provenance' or 'provenance_and_confidence' depending on entity type.
    """
    total_entities = 0
    provenance_count = 0

    for entity_type in EntityType:
        entities = kg.list_entities(entity_type, limit=100)
        for entity in entities:
            total_entities += 1
            try:
                # Check for provenance or provenance_and_confidence
                prov = getattr(entity, "provenance", None)
                prov_and_conf = getattr(entity, "provenance_and_confidence", None)

                # Handle both dict and Pydantic model instances
                if prov is not None:
                    if (
                        isinstance(prov, dict)
                        and len(prov) > 0
                        or hasattr(prov, "primary_data_source")
                        and prov.primary_data_source
                    ):
                        provenance_count += 1
                elif prov_and_conf is not None and (
                    isinstance(prov_and_conf, dict)
                    and len(prov_and_conf) > 0
                    or hasattr(prov_and_conf, "primary_data_source")
                    and prov_and_conf.primary_data_source
                ):
                    provenance_count += 1
            except (AttributeError, KeyError):
                pass

    score = provenance_count / total_entities if total_entities > 0 else 0.0
    report.provenance_coverage = score

    if score < 0.5:
        report.warnings.append(
            f"Low provenance coverage: {score:.1%} of entities have provenance set"
        )
        report.enrichment_recommendations.append(
            "Enrich provenance metadata to track source and confidence of enriched data"
        )

    return score
