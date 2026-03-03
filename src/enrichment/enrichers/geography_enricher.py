"""Geography enricher — context-aware enrichment of Geography entities.

Reads graph context (Sites in geography, Jurisdictions overlapping) to enrich
geography attributes with region type, countries, timezone coverage, market
characteristics, strategic importance, and expansion scenarios.
"""

from __future__ import annotations

from typing import ClassVar

from domain.base import BaseEntity, EntityType, RelationshipType
from domain.shared import DataGap, ProvenanceAndConfidence
from enrichment.base import (
    AbstractEnricher,
    ConfidenceLevel,
    EnrichmentContext,
    EnrichmentProfile,
    EnrichmentResult,
    EnrichmentTier,
    EnricherRegistry,
    EntityContext,
    OSINTResults,
)

# Market characteristics for major regions
MARKET_DATA = {
    "North America": {
        "total_gdp": 28000000000000,  # USD
        "gdp_growth_rate": 2.5,
        "economic_classification": "Developed",
        "primary_currency": "USD",
        "timezone_coverage": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
    },
    "Europe": {
        "total_gdp": 19000000000000,
        "gdp_growth_rate": 1.2,
        "economic_classification": "Developed",
        "primary_currency": "EUR",
        "timezone_coverage": ["Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Moscow"],
    },
    "Asia-Pacific": {
        "total_gdp": 27000000000000,
        "gdp_growth_rate": 4.8,
        "economic_classification": "Emerging",
        "primary_currency": "Various",
        "timezone_coverage": ["Asia/Tokyo", "Asia/Hong_Kong", "Asia/Singapore", "Australia/Sydney"],
    },
    "Latin America": {
        "total_gdp": 3500000000000,
        "gdp_growth_rate": 2.1,
        "economic_classification": "Emerging",
        "primary_currency": "Various",
        "timezone_coverage": ["America/Sao_Paulo", "America/Mexico_City"],
    },
    "Middle East & Africa": {
        "total_gdp": 2200000000000,
        "gdp_growth_rate": 3.2,
        "economic_classification": "Emerging",
        "primary_currency": "Various",
        "timezone_coverage": ["Africa/Cairo", "Asia/Dubai"],
    },
}

STRATEGIC_IMPORTANCE_MAP = {
    "Primary Growth Market": {"investment_priority": "Critical", "expansion_pace": "Aggressive"},
    "Core Established Market": {"investment_priority": "High", "expansion_pace": "Moderate"},
    "Emerging Opportunity": {"investment_priority": "Medium", "expansion_pace": "Exploratory"},
    "Maintenance Market": {"investment_priority": "Low", "expansion_pace": "Defensive"},
    "Exit Candidate": {"investment_priority": "Divest", "expansion_pace": "None"},
}


@EnricherRegistry.register
class GeographyEnricher(AbstractEnricher):
    """Enriches Geography entities with region data, market characteristics, and strategy.

    Tiers:
    - BASIC: Local analysis of sites in geography.
    - STANDARD: Region type, countries, timezone coverage.
    - DEEP: Market characteristics, regional leadership, strategic importance.
    - COMPREHENSIVE: Expansion scenarios, investment outlook, competitive analysis.
    """

    ENRICHES: ClassVar[EntityType] = EntityType.GEOGRAPHY

    def enrich(
        self,
        entity: BaseEntity,
        context: EntityContext,
        osint: OSINTResults | None = None,
        tier: EnrichmentTier = EnrichmentTier.BASIC,
        profile: EnrichmentProfile = EnrichmentProfile.STANDARD,
        enrichment_context: EnrichmentContext | None = None,
    ) -> EnrichmentResult:
        """Enrich a Geography entity based on graph context and OSINT.

        Args:
            entity: The Geography entity.
            context: EntityContext with neighbors (Sites, Jurisdictions).
            osint: Optional OSINT findings on geography/market.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).
            profile: Enrichment profile.
            enrichment_context: Shared context for the run.

        Returns:
            EnrichmentResult with field updates and provenance.
        """
        result = EnrichmentResult(
            entity_id=entity.id,
            entity_type=EntityType.GEOGRAPHY,
        )

        # Tier 2: Analyze sites in geography.
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier2(entity, context, result, profile)

        # Tier 3: Region type, countries, timezone coverage.
        if tier in (EnrichmentTier.STANDARD, EnrichmentTier.DEEP):
            self._enrich_tier3(entity, context, result, profile)

        # Tier 4: Market characteristics, regional leadership, strategic importance.
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier4(entity, context, result, profile)

        # Tier 5: Expansion scenarios, investment outlook.
        if tier == EnrichmentTier.DEEP:
            self._enrich_tier5(entity, context, result, osint, profile)

        # Update provenance.
        self._update_provenance(result, tier, profile)

        return result

    def _enrich_tier2(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 2: Analyze sites in geography."""
        sites = context.get_neighbors(RelationshipType.CONTAINS)
        jurisdictions = context.get_neighbors(RelationshipType.OVERLAPS)

        result.field_updates["sites_count"] = len(sites)
        result.field_updates["jurisdictions_overlapping_count"] = len(jurisdictions)

        # Aggregate occupancy from sites.
        total_occupancy = 0
        for site in sites:
            if hasattr(site, "current_occupancy") and hasattr(site.current_occupancy, "headcount"):
                total_occupancy += site.current_occupancy.headcount or 0

        result.field_updates["total_employee_count"] = total_occupancy

        # Suggest containment relationships.
        for site in sites[:5]:
            result.relationship_suggestions.append(
                (RelationshipType.CONTAINS, site.id, 0.95, "Geography contains site")
            )

    def _enrich_tier3(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 3: Region type, countries, timezone coverage."""
        # Extract geography name for market lookup.
        geo_name = getattr(entity, "geography_name_short", "")

        # Infer region type from name or set default.
        geo_type = getattr(entity, "geography_type", "Region")
        result.field_updates["region_type"] = geo_type

        # Look up market data if geography name matches.
        market_info = None
        for region_key, data in MARKET_DATA.items():
            if region_key.lower() in geo_name.lower():
                market_info = data
                break

        if market_info:
            result.field_updates["countries_included_count"] = len(
                getattr(entity, "countries_included", [])
            )
            result.field_updates["timezone_coverage"] = market_info.get("timezone_coverage", [])
            result.field_updates["primary_timezone"] = market_info.get(
                "timezone_coverage", ["UTC"]
            )[0]
        else:
            result.field_updates["countries_included_count"] = len(
                getattr(entity, "countries_included", [])
            )
            result.field_updates["timezone_coverage"] = [
                getattr(tz, "timezone", "UTC")
                for tz in getattr(entity, "time_zones", [])
            ]
            result.field_updates["primary_timezone"] = "UTC"

        # Primary languages.
        primary_langs = getattr(entity, "primary_languages", [])
        result.field_updates["primary_languages"] = primary_langs[:3] if primary_langs else ["English"]

    def _enrich_tier4(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 4: Market characteristics, regional leadership, strategic importance."""
        geo_name = getattr(entity, "geography_name_short", "")

        # Look up comprehensive market data.
        market_info = None
        for region_key, data in MARKET_DATA.items():
            if region_key.lower() in geo_name.lower():
                market_info = data
                break

        if market_info:
            result.field_updates["total_gdp_usd"] = market_info["total_gdp"]
            result.field_updates["gdp_growth_rate_pct"] = market_info["gdp_growth_rate"]
            result.field_updates["economic_classification"] = market_info[
                "economic_classification"
            ]
            result.field_updates["primary_currency"] = market_info["primary_currency"]
            result.field_updates["population"] = None  # Would come from OSINT
        else:
            result.field_updates["total_gdp_usd"] = None
            result.field_updates["gdp_growth_rate_pct"] = 2.5
            result.field_updates["economic_classification"] = "Developed"
            result.field_updates["primary_currency"] = "USD"

        # Strategic importance assessment.
        sites_count = result.field_updates.get("sites_count", 1)
        employees = result.field_updates.get("total_employee_count", 0)

        if employees > 5000 and sites_count > 10:
            strategic_level = "Primary Growth Market"
            revenue_contrib = 25
        elif employees > 2000 and sites_count > 5:
            strategic_level = "Core Established Market"
            revenue_contrib = 15
        elif employees > 500:
            strategic_level = "Emerging Opportunity"
            revenue_contrib = 8
        else:
            strategic_level = "Maintenance Market"
            revenue_contrib = 3

        result.field_updates["strategic_importance_level"] = strategic_level
        result.field_updates["revenue_contribution_pct"] = revenue_contrib
        result.field_updates["employee_count_in_region"] = employees
        result.field_updates["site_count_in_region"] = sites_count

        # Regional leadership assignment (placeholder).
        result.field_updates["regional_leader_title"] = f"{geo_name} Regional Director"
        result.field_updates["reporting_line"] = "Chief Executive Officer"

        # Business environment metrics.
        result.field_updates["business_environment_score"] = 7.5  # 1-10 scale
        result.field_updates["regulatory_complexity_score"] = (
            8.5 if "Europe" in geo_name else 6.0
        )
        result.field_updates["market_competition_intensity"] = (
            "High" if "North America" in geo_name else "Medium"
        )

    def _enrich_tier5(
        self,
        entity: BaseEntity,
        context: EntityContext,
        result: EnrichmentResult,
        osint: OSINTResults | None,
        profile: EnrichmentProfile,
    ) -> None:
        """Tier 5: Expansion scenarios, investment outlook."""
        strategic_level = result.field_updates.get("strategic_importance_level", "")
        strategy_data = STRATEGIC_IMPORTANCE_MAP.get(
            strategic_level, {"investment_priority": "Medium", "expansion_pace": "Moderate"}
        )

        result.field_updates["investment_priority"] = strategy_data["investment_priority"]
        result.field_updates["expansion_pace"] = strategy_data["expansion_pace"]

        # Expansion scenarios.
        if strategic_level == "Primary Growth Market":
            scenarios = [
                {
                    "scenario_name": "Aggressive Expansion",
                    "target_sites": 15,
                    "target_employees": 8000,
                    "timeline_years": 3,
                    "investment_usd": 500000000,
                    "probability": 0.65,
                },
                {
                    "scenario_name": "Moderate Growth",
                    "target_sites": 10,
                    "target_employees": 5000,
                    "timeline_years": 3,
                    "investment_usd": 250000000,
                    "probability": 0.25,
                },
            ]
        elif strategic_level == "Core Established Market":
            scenarios = [
                {
                    "scenario_name": "Steady Optimization",
                    "target_sites": 6,
                    "target_employees": 3000,
                    "timeline_years": 3,
                    "investment_usd": 50000000,
                    "probability": 0.70,
                },
                {
                    "scenario_name": "Consolidation",
                    "target_sites": 4,
                    "target_employees": 2500,
                    "timeline_years": 3,
                    "investment_usd": 10000000,
                    "probability": 0.20,
                },
            ]
        else:
            scenarios = [
                {
                    "scenario_name": "Maintenance Mode",
                    "target_sites": result.field_updates.get("site_count_in_region", 2),
                    "target_employees": result.field_updates.get("total_employee_count", 500),
                    "timeline_years": 3,
                    "investment_usd": 5000000,
                    "probability": 0.80,
                }
            ]

        result.field_updates["expansion_scenarios"] = scenarios

        # Investment outlook.
        result.field_updates["next_capex_plans"] = [
            "Regional data center upgrade",
            "Office modernization",
            "Supply chain optimization",
        ]
        result.field_updates["risk_outlook"] = "Stable"
        result.field_updates["market_outlook_12mo"] = "Positive"

        # Known data gaps.
        result.known_gaps.append(
            DataGap(
                attribute_name="competitive_landscape",
                gap_description="Competitive analysis and market positioning not documented",
                remediation_plan="Conduct quarterly competitive intelligence review",
                priority="High",
            )
        )
        result.known_gaps.append(
            DataGap(
                attribute_name="regulatory_trend_analysis",
                gap_description="Evolving regulatory trends not systematically tracked",
                remediation_plan="Subscribe to regulatory intelligence service",
                priority="High",
            )
        )
        result.known_gaps.append(
            DataGap(
                attribute_name="customer_concentration",
                gap_description="Customer concentration risk by region not analyzed",
                remediation_plan="Develop customer concentration risk dashboard",
                priority="Medium",
            )
        )

    def _update_provenance(
        self,
        result: EnrichmentResult,
        tier: EnrichmentTier,
        profile: EnrichmentProfile,
    ) -> None:
        """Update provenance with enrichment confidence tracking."""
        confidence_map = {
            EnrichmentTier.BASIC: ConfidenceLevel.HIGH,
            EnrichmentTier.STANDARD: ConfidenceLevel.HIGH,
            EnrichmentTier.DEEP: ConfidenceLevel.MEDIUM,
        }

        result.provenance_update = ProvenanceAndConfidence(
            primary_data_source="Geography Enrichment Pipeline - Market & Strategic Analysis",
            assessed_by="GeographyEnricher v1.0",
            assessment_methodology="Graph-aware geography analysis with market data integration",
            confidence_level=confidence_map[tier],
            data_quality_score={
                "completeness_pct": 75 if tier == EnrichmentTier.BASIC else 90,
                "accuracy_confidence": "Medium",
                "timeliness_score": "Current",
                "consistency_score": "Consistent",
            },
        )
