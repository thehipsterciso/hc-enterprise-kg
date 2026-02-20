"""Site entity — physical location in the enterprise estate.

Full enterprise ontology entity (~91 attributes across 9 groups): identity &
classification, physical characteristics, infrastructure & utilities, financial
profile, capacity & utilization, risk & resilience, dependencies, temporal, and
provenance. Part of L07: Locations & Facilities layer. Derived from L3 schema.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import ProvenanceAndConfidence, TemporalAndVersioning

# ---------------------------------------------------------------------------
# Sub-models — Group 1: Identity & Classification
# ---------------------------------------------------------------------------


class SiteLocalName(BaseModel):
    """Multi-lingual name for a site."""

    language_code: str = ""  # ISO 639-1
    name: str = ""
    locale: str = ""  # ISO 3166-1 alpha-2


class SiteFormerName(BaseModel):
    """Historical name of a site."""

    former_name: str = ""
    from_date: str | None = None
    to_date: str | None = None
    change_reason: str = ""


class SiteAcquisitionSource(BaseModel):
    """Acquisition source for an acquired site."""

    source_entity_name: str = ""
    acquisition_date: str | None = None
    deal_reference: str = ""


class SiteAddress(BaseModel):
    """Physical address of a site."""

    street_line_1: str = ""
    street_line_2: str = ""
    city: str = ""
    state_province: str = ""
    postal_code: str = ""
    country_code: str = ""  # ISO 3166-1 alpha-2
    country_name: str = ""
    formatted_address: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 2: Physical Characteristics
# ---------------------------------------------------------------------------


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float | None = None  # -90 to 90
    longitude: float | None = None  # -180 to 180


class AreaMeasurement(BaseModel):
    """Area measurement with unit."""

    value: float | None = None
    unit: str = "sqft"  # sqft, sqm


class DesignCapacity(BaseModel):
    """Site design capacity."""

    max_occupants: int | None = None
    max_workstations: int | None = None
    current_configured_workstations: int | None = None
    current_utilization_pct: float | None = None  # 0-100


class FacilityConditionIndex(BaseModel):
    """Facility condition assessment (RICS standard)."""

    score: float | None = None  # 0-1
    condition_rating: str = ""  # Good, Fair, Poor, Critical
    assessed_date: str | None = None


class EnvironmentalCertification(BaseModel):
    """Environmental/sustainability certification."""

    certification: str = ""
    # Enum: LEED, BREEAM, WELL, ISO 14001, ISO 50001, ENERGY STAR,
    # Green Globes, NABERS, Other
    level: str = ""
    date_achieved: str | None = None
    expiration_date: str | None = None


class AccessibilityCompliance(BaseModel):
    """Accessibility compliance status."""

    standard: str = ""
    compliance_status: str = ""
    # Enum: Fully Compliant, Substantially Compliant, Partially Compliant,
    # Non-Compliant, Exempt, Not Assessed
    last_assessment_date: str | None = None
    remediation_plan: str = ""


class ParkingCapacity(BaseModel):
    """Parking facility details."""

    total_spaces: int | None = None
    ev_charging_spaces: int | None = None
    accessible_spaces: int | None = None
    parking_type: str = ""  # Surface Lot, Structured Garage, Underground, Mixed, None


# ---------------------------------------------------------------------------
# Sub-models — Group 3: Infrastructure & Utilities
# ---------------------------------------------------------------------------


class BackupGenerator(BaseModel):
    """Backup generator details."""

    has_generator: bool = False
    generator_capacity_kw: float | None = None
    fuel_type: str = ""
    fuel_runtime_hours: float | None = None
    last_test_date: str | None = None


class UPSCapacity(BaseModel):
    """UPS system details."""

    has_ups: bool = False
    ups_capacity_kva: float | None = None
    runtime_minutes: float | None = None


class PowerSupply(BaseModel):
    """Power supply infrastructure."""

    primary_source: str = ""
    # Enum: Grid — Single Feed, Grid — Dual Feed, Grid — Diverse Substation,
    # On-Site Generation, Renewable — On-Site, Hybrid
    total_capacity_kw: float | None = None
    current_load_kw: float | None = None
    redundancy_level: str = ""  # N, N+1, 2N, 2N+1
    backup_generator: BackupGenerator = Field(default_factory=BackupGenerator)
    ups_capacity: UPSCapacity = Field(default_factory=UPSCapacity)
    renewable_energy_pct: float | None = None  # 0-100


class NetworkConnectivity(BaseModel):
    """Network connectivity details."""

    primary_carrier: str = ""
    secondary_carrier: str = ""
    redundancy_level: str = ""
    # Enum: Single Provider, Dual Provider, Diverse Path,
    # Carrier Diverse + Path Diverse
    bandwidth_mbps: float | None = None
    latency_to_primary_dc_ms: float | None = None
    last_mile_type: str = ""
    # Enum: Fiber, Cable, DSL, Fixed Wireless, Satellite, 5G, Leased Line
    sd_wan_enabled: bool | None = None


class CoolingCapacity(BaseModel):
    """Cooling infrastructure (Data Center / Manufacturing)."""

    cooling_type: str = ""
    # Enum: Air Cooled, Water Cooled, Free Cooling, Liquid Cooling, Hybrid
    total_capacity_kw: float | None = None
    redundancy_level: str = ""  # N, N+1, 2N, 2N+1
    pue: float | None = None  # 1.0-3.0


class WaterConsumption(BaseModel):
    """Water consumption measurement."""

    volume: float | None = None
    unit: str = "gallons"  # gallons, liters, cubic_meters


class WaterSupply(BaseModel):
    """Water supply infrastructure (Manufacturing)."""

    source: str = ""  # Municipal, Well, Recycled, Desalination, Mixed
    treatment_on_site: bool = False
    redundancy: str = ""  # Single Source, Dual Source, On-Site Storage
    daily_consumption: WaterConsumption = Field(default_factory=WaterConsumption)


class RegulatoryPermit(BaseModel):
    """Environmental/waste regulatory permit."""

    permit_type: str = ""
    issuing_authority: str = ""
    expiration_date: str | None = None


class WasteManagement(BaseModel):
    """Waste management details."""

    hazardous_materials_present: bool = False
    hazardous_materials_types: list[str] = Field(default_factory=list)
    waste_classification: str = ""
    # Enum: General Commercial, Industrial, Hazardous, Mixed
    disposal_method: str = ""
    regulatory_permits: list[RegulatoryPermit] = Field(default_factory=list)


class PhysicalSecuritySystem(BaseModel):
    """Physical security system."""

    system_type: str = ""
    # Enum: Access Control — Card/Badge, Biometric, Multi-Factor,
    # CCTV — Analog/IP/AI-Enabled, Intrusion Detection, Guard Service, etc.
    coverage: str = ""  # Full Site, Perimeter Only, Critical Areas Only, Partial
    monitoring: str = ""
    # Enum: 24x7 Live Monitoring, Business Hours Monitoring,
    # Recorded — Review on Alert, Not Monitored
    vendor: str = ""
    contract_expiration: str | None = None


class FireSuppression(BaseModel):
    """Fire suppression system."""

    system_type: str = ""
    # Enum: Wet Sprinkler, Dry Sprinkler, Pre-Action,
    # Clean Agent (FM-200/Novec), Inert Gas, Foam, None
    coverage: str = ""  # Full Building, Critical Areas Only, Partial
    last_inspection_date: str | None = None
    next_inspection_date: str | None = None
    compliance_status: str = ""
    # Enum: Compliant, Deficiency Noted, Non-Compliant, Not Inspected


class EnvironmentalControls(BaseModel):
    """Environmental control systems."""

    temperature_controlled: bool = False
    temperature_range: str = ""
    humidity_controlled: bool = False
    humidity_range: str = ""
    clean_room_classification: str = ""  # ISO Class 1-8, Not Classified, Not Applicable


class SpecialInfrastructure(BaseModel):
    """Special infrastructure item."""

    infrastructure_type: str = ""
    capacity: str = ""
    condition: str = ""  # Good, Fair, Poor, Not Assessed


# ---------------------------------------------------------------------------
# Sub-models — Group 4: Financial Profile
# ---------------------------------------------------------------------------


class AnnualCost(BaseModel):
    """Annual cost with currency."""

    amount: float | None = None
    currency: str = "USD"  # ISO 4217
    fiscal_year: str = ""


class SiteCostBreakdownItem(BaseModel):
    """Site operating cost breakdown."""

    category: str = ""
    # Enum: Lease / Mortgage, Utilities — Electric/Gas/Water/Other,
    # Maintenance — Preventive/Reactive, Insurance, Security, Property Tax,
    # Cleaning & Janitorial, Landscaping, Waste Disposal, Capital Maintenance, Other
    amount: float | None = None
    percentage_of_total: float | None = None


class LeaseDetails(BaseModel):
    """Lease terms and financials."""

    landlord: str = ""
    lease_type: str = ""
    # Enum: Full Service / Gross, Modified Gross, Triple Net (NNN),
    # Absolute Net, Ground Lease
    lease_start_date: str | None = None
    lease_end_date: str | None = None
    annual_base_rent: float | None = None
    currency: str = "USD"  # ISO 4217
    escalation_terms: str = ""
    break_clause_dates: list[str] = Field(default_factory=list)
    renewal_options: str = ""
    notice_period_months: int | None = None
    security_deposit: float | None = None
    tenant_improvement_allowance: float | None = None
    sublease_permitted: bool | None = None
    assignment_permitted: bool | None = None
    remaining_lease_obligation: float | None = None


class CapitalInvestment(BaseModel):
    """Planned capital investment."""

    investment_description: str = ""
    amount: float | None = None
    currency: str = "USD"  # ISO 4217
    investment_type: str = ""
    # Enum: Expansion, Renovation, Technology Upgrade,
    # Compliance / Safety, Sustainability, Deferred Maintenance
    timeline: str = ""
    approval_status: str = ""  # Approved, Pending Approval, Proposed, Deferred


class Valuation(BaseModel):
    """Asset valuation."""

    value: float | None = None
    currency: str = "USD"  # ISO 4217
    valuation_date: str | None = None
    valuation_method: str = ""


class BookValue(BaseModel):
    """Book value for owned property."""

    value: float | None = None
    currency: str = "USD"  # ISO 4217
    as_of_date: str | None = None


class CostPerUnit(BaseModel):
    """Cost per unit metrics."""

    cost_per_sqft: float | None = None
    cost_per_occupant: float | None = None
    unit: str = "sqft"  # sqft, sqm


class DeferredMaintenancePriority(BaseModel):
    """Deferred maintenance priority breakdown item."""

    priority: str = ""
    # Enum: Critical — Safety / Compliance, High — Operational Impact,
    # Medium — Efficiency / Comfort, Low — Cosmetic / Deferred
    amount: float | None = None


class DeferredMaintenanceBacklog(BaseModel):
    """Deferred maintenance backlog."""

    total_amount: float | None = None
    currency: str = "USD"  # ISO 4217
    priority_breakdown: list[DeferredMaintenancePriority] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Sub-models — Group 5: Capacity & Utilization
# ---------------------------------------------------------------------------


class CurrentOccupancy(BaseModel):
    """Current site occupancy."""

    headcount: int | None = None
    as_of_date: str | None = None


class OccupancyByUnit(BaseModel):
    """Occupancy breakdown by organizational unit."""

    unit_id: str = ""
    unit_name: str = ""
    headcount: int | None = None
    area_allocated: AreaMeasurement = Field(default_factory=AreaMeasurement)


class UtilizationRate(BaseModel):
    """Space utilization metrics."""

    current_pct: float | None = None  # 0-100
    peak_pct: float | None = None  # 0-100
    measurement_methodology: str = ""
    # Enum: Badge Swipe Data, Sensor-Based Occupancy, WiFi Connection Count,
    # Manual Count, Estimated
    measurement_period: str = ""


class AvailableCapacity(BaseModel):
    """Available capacity at a site."""

    available_workstations: int | None = None
    available_area: AreaMeasurement = Field(default_factory=AreaMeasurement)
    available_specialized_capacity: str = ""


class CapacityForecast(BaseModel):
    """Capacity projection."""

    projected_occupancy: int | None = None
    projection_date: str | None = None
    growth_rate_assumption: float | None = None
    forecast_methodology: str = ""


class SeasonalVariation(BaseModel):
    """Seasonal occupancy pattern."""

    has_seasonal_pattern: bool = False
    peak_period: str = ""
    low_period: str = ""
    variation_pct: float | None = None


class ExpansionCost(BaseModel):
    """Estimated expansion cost."""

    amount: float | None = None
    currency: str = "USD"  # ISO 4217


class ExpansionPotential(BaseModel):
    """Site expansion potential."""

    expandable: bool = False
    expansion_type: str = ""
    # Enum: Vertical (Additional Floors), Horizontal (Adjacent Land),
    # Densification (More Workstations), Repurpose Existing Space, None
    max_additional_capacity: str = ""
    estimated_expansion_cost: ExpansionCost = Field(default_factory=ExpansionCost)
    zoning_permits_required: bool | None = None


# ---------------------------------------------------------------------------
# Sub-models — Group 6: Risk & Resilience
# ---------------------------------------------------------------------------


class NaturalHazard(BaseModel):
    """Natural hazard risk profile."""

    hazard_type: str = ""
    # Enum: Seismic, Flood — Riverine/Coastal/Pluvial, Hurricane, Tornado,
    # Wildfire, Tsunami, Volcanic, Extreme Heat/Cold, Drought,
    # Landslide / Subsidence, Wind, Hail
    risk_level: str = ""  # Very High, High, Moderate, Low, Negligible
    basis: str = ""
    return_period: str = ""


class ClimateRiskAssessment(BaseModel):
    """Climate risk assessment (TCFD/IFRS S2)."""

    physical_risk_score: float | None = None  # 1.0-5.0
    physical_risk_drivers: list[str] = Field(default_factory=list)
    transition_risk_score: float | None = None  # 1.0-5.0
    transition_risk_drivers: list[str] = Field(default_factory=list)
    scenario: str = ""
    time_horizon: str = ""
    assessment_methodology: str = ""
    assessed_date: str | None = None


class GeopoliticalRisk(BaseModel):
    """Geopolitical risk assessment."""

    risk_level: str = ""  # Critical, High, Elevated, Moderate, Low
    risk_factors: list[str] = Field(default_factory=list)
    political_stability_index: float | None = None
    last_assessment_date: str | None = None


class CrimeEnvironment(BaseModel):
    """Local crime environment assessment."""

    crime_index: float | None = None
    assessment_source: str = ""
    specific_concerns: list[str] = Field(default_factory=list)
    last_updated: str | None = None


class ProximityDistance(BaseModel):
    """Distance measurement."""

    value: float | None = None
    unit: str = "km"  # km, miles


class ProximityRisk(BaseModel):
    """Proximity-based risk."""

    risk_type: str = ""
    # Enum: Flood Plain, Industrial Hazard, Airport / Flight Path,
    # Military Installation, Nuclear Facility, Chemical Storage, etc.
    distance: ProximityDistance = Field(default_factory=ProximityDistance)
    description: str = ""


class EvacuationPlan(BaseModel):
    """Site evacuation plan."""

    plan_reference: str = ""
    last_drill_date: str | None = None
    next_drill_date: str | None = None
    max_evacuation_time_minutes: int | None = None
    assembly_points: int | None = None
    drill_results: str = ""
    # Enum: Successful, Successful with Observations,
    # Failed — Corrective Actions Required, Not Conducted


class CoverageAmount(BaseModel):
    """Insurance coverage amount."""

    limit: float | None = None
    deductible: float | None = None
    currency: str = "USD"  # ISO 4217


class BusinessInterruptionCoverage(BaseModel):
    """Business interruption insurance."""

    limit: float | None = None
    waiting_period_hours: float | None = None
    indemnity_period_months: int | None = None
    currency: str = "USD"  # ISO 4217


class LiabilityCoverage(BaseModel):
    """Liability insurance coverage."""

    limit: float | None = None
    currency: str = "USD"  # ISO 4217


class InsuranceCoverage(BaseModel):
    """Site insurance coverage."""

    property_coverage: CoverageAmount = Field(default_factory=CoverageAmount)
    business_interruption_coverage: BusinessInterruptionCoverage = Field(
        default_factory=BusinessInterruptionCoverage
    )
    liability_coverage: LiabilityCoverage = Field(default_factory=LiabilityCoverage)
    carrier: str = ""
    policy_reference: str = ""
    renewal_date: str | None = None


class SiteSPOF(BaseModel):
    """Single point of failure for a site."""

    spof_id: str = ""
    spof_description: str = ""
    spof_type: str = ""
    # Enum: Power, Network, Cooling, Water, Physical Access,
    # Key Personnel, Vendor Dependency, Equipment
    mitigation_status: str = ""
    # Enum: Mitigated, Partially Mitigated, Unmitigated, Accepted
    mitigation_plan: str = ""


class SiteIncident(BaseModel):
    """Last incident at a site."""

    incident_type: str = ""
    incident_date: str | None = None
    severity: str = ""  # Critical, Major, Moderate, Minor
    impact_description: str = ""
    resolution: str = ""
    lessons_learned_reference: str = ""


# ---------------------------------------------------------------------------
# Sub-models — Group 7: Dependencies & Relationships
# ---------------------------------------------------------------------------


class GeographyReference(BaseModel):
    """Geography containment reference."""

    geography_id: str = ""
    geography_level: str = ""


class JurisdictionReference(BaseModel):
    """Jurisdiction applicability reference."""

    jurisdiction_id: str = ""
    jurisdiction_type: str = ""


class SiteConnection(BaseModel):
    """Connection between sites."""

    site_id: str = ""
    connection_type: str = ""
    # Enum: Network — WAN/Dedicated Circuit/VPN,
    # Logistics — Road/Rail/Sea/Air,
    # Supply Chain — Upstream/Downstream
    capacity: str = ""
    latency: str = ""


class SystemHosting(BaseModel):
    """System hosted at a site."""

    system_id: str = ""
    hosting_type: str = ""
    # Enum: Primary Production, Disaster Recovery, Development / Test, Staging


class VendorService(BaseModel):
    """Vendor-managed service at a site."""

    vendor_id: str = ""
    service_type: str = ""
    # Enum: Facility Management, Physical Security, Cleaning / Janitorial,
    # Catering, IT Infrastructure, Grounds Maintenance, Waste Management,
    # Specialized Maintenance


# ---------------------------------------------------------------------------
# Main entity
# ---------------------------------------------------------------------------


class Site(BaseEntity):
    """Represents a physical site in the enterprise estate.

    Full enterprise ontology entity (~91 attributes across 9 groups).
    Models physical locations including offices, data centers, manufacturing
    plants, and warehouses with infrastructure, financial, and risk profiles.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.SITE
    entity_type: Literal[EntityType.SITE] = EntityType.SITE

    # --- Group 1: Identity & Classification ---
    site_id: str = ""  # ST-XXXXX
    site_description: str = ""
    site_type: str = ""
    # Enum: Corporate Headquarters, Regional Headquarters, Office,
    # Manufacturing Plant, Distribution Center, Data Center, R&D Facility,
    # Laboratory, Warehouse, Co-Working / Flex Space, etc.
    site_subtype: str = ""
    site_status: str = ""
    # Enum: Active, Under Construction, Planned, Temporarily Closed,
    # Reduced Operations, Decommissioning, Closed, Sold / Exited
    site_status_rationale: str = ""
    ownership_type: str = ""
    # Enum: Owned — Freehold, Owned — Leasehold, Leased, Subleased,
    # Co-Located, Managed Service, License Agreement, Virtual
    strategic_designation: str = ""
    # Enum: Flagship, Core Operations, Satellite, Flex / Surge,
    # Legacy, Divestiture Candidate
    origin: str = ""
    # Enum: Organic — Purpose Built, Organic — Leased, Acquired,
    # Leased Post-Acquisition, Joint Venture, Greenfield Build, Inherited
    site_name_local: list[SiteLocalName] = Field(default_factory=list)
    site_name_former: list[SiteFormerName] = Field(default_factory=list)
    acquisition_source: SiteAcquisitionSource | None = None
    address: SiteAddress = Field(default_factory=SiteAddress)

    # --- Group 2: Physical Characteristics ---
    coordinates: Coordinates = Field(default_factory=Coordinates)
    total_area: AreaMeasurement | None = None
    usable_area: AreaMeasurement | None = None
    building_count: int | None = None
    floors: int | None = None
    year_built: int | None = None
    year_last_renovated: int | None = None
    design_capacity: DesignCapacity | None = None
    facility_condition_index: FacilityConditionIndex | None = None
    environmental_certifications: list[EnvironmentalCertification] = Field(
        default_factory=list
    )
    accessibility_compliance: AccessibilityCompliance | None = None
    parking_capacity: ParkingCapacity | None = None

    # --- Group 3: Infrastructure & Utilities ---
    power_supply: PowerSupply | None = None
    network_connectivity: NetworkConnectivity | None = None
    cooling_capacity: CoolingCapacity | None = None
    water_supply: WaterSupply | None = None
    waste_management: WasteManagement | None = None
    physical_security_tier: str = ""
    # Enum: Tier 1 — Basic, Tier 2 — Enhanced, Tier 3 — Monitored,
    # Tier 4 — High Security, Tier 5 — Restricted / Classified
    physical_security_systems: list[PhysicalSecuritySystem] = Field(
        default_factory=list
    )
    fire_suppression: FireSuppression | None = None
    environmental_controls: EnvironmentalControls | None = None
    special_infrastructure: list[SpecialInfrastructure] = Field(default_factory=list)

    # --- Group 4: Financial Profile ---
    annual_operating_cost: AnnualCost = Field(default_factory=AnnualCost)
    cost_breakdown: list[SiteCostBreakdownItem] = Field(default_factory=list)
    lease_details: LeaseDetails | None = None
    capital_investment_planned: list[CapitalInvestment] = Field(default_factory=list)
    replacement_value: Valuation | None = None
    book_value: BookValue | None = None
    cost_per_unit: CostPerUnit | None = None
    cost_benchmark: Valuation | None = None  # Reuse Valuation for benchmark
    deferred_maintenance_backlog: DeferredMaintenanceBacklog | None = None

    # --- Group 5: Capacity & Utilization ---
    current_occupancy: CurrentOccupancy = Field(default_factory=CurrentOccupancy)
    occupancy_by_unit: list[OccupancyByUnit] = Field(default_factory=list)
    utilization_rate: UtilizationRate | None = None
    available_capacity: AvailableCapacity | None = None
    capacity_forecast: CapacityForecast | None = None
    shift_model: str = ""
    # Enum: Single Shift, Two Shifts, Three Shifts, Continuous (24x7),
    # Not Applicable
    seasonal_variation: SeasonalVariation | None = None
    expansion_potential: ExpansionPotential | None = None

    # --- Group 6: Risk & Resilience ---
    risk_exposure_inherent: str = ""  # Critical, High, Medium, Low
    risk_exposure_residual: str = ""  # Critical, High, Medium, Low
    natural_hazard_profile: list[NaturalHazard] = Field(default_factory=list)
    climate_risk_assessment: ClimateRiskAssessment | None = None
    geopolitical_risk: GeopoliticalRisk | None = None
    crime_environment: CrimeEnvironment | None = None
    proximity_risks: list[ProximityRisk] = Field(default_factory=list)
    business_continuity_tier: str = ""  # Platinum, Gold, Silver, Bronze
    disaster_recovery_role: str = ""
    # Enum: Primary Production Site, DR Site — Hot/Warm/Cold Standby,
    # Alternate Work Site, Not Designated
    evacuation_plan: EvacuationPlan | None = None
    insurance_coverage: InsuranceCoverage | None = None
    single_points_of_failure: list[SiteSPOF] = Field(default_factory=list)
    last_incident: SiteIncident | None = None

    # --- Group 7: Dependencies & Relationships ---
    located_in_geography: list[GeographyReference] = Field(default_factory=list)
    subject_to_jurisdictions: list[JurisdictionReference] = Field(default_factory=list)
    connected_to_sites: list[SiteConnection] = Field(default_factory=list)
    backup_site: str = ""  # Site ID
    houses_org_units: list[str] = Field(default_factory=list)
    employs_persons: list[str] = Field(default_factory=list)
    hosts_systems: list[SystemHosting] = Field(default_factory=list)
    stores_data: list[str] = Field(default_factory=list)
    serves_customers_from: list[str] = Field(default_factory=list)
    managed_by_vendors: list[VendorService] = Field(default_factory=list)
    governed_by: list[str] = Field(default_factory=list)
    subject_to_initiatives: list[str] = Field(default_factory=list)

    # --- Group 8: Temporal & Versioning (shared) ---
    temporal: TemporalAndVersioning = Field(default_factory=TemporalAndVersioning)

    # --- Group 9: Provenance & Confidence (shared) ---
    provenance: ProvenanceAndConfidence = Field(default_factory=ProvenanceAndConfidence)
