"""Contract entity — vendor/partner contract in the knowledge graph.

Covers MSAs, SOWs, software licenses, SaaS subscriptions, supply
agreements, NDAs, DPAs, and other commercial agreements.

Attribute groups
----------------
1. Identity (~5 attrs)
2. Parties & Ownership (~5 attrs)
3. Financial Terms (~5 attrs)
4. Duration & Renewal (~9 attrs)
5. Termination (~4 attrs)
6. SLAs (~1 attr)
7. Key Provisions (~5 attrs)
8. Amendments & Related (~2 attrs)
9. Dependencies & Relationships (~4 attrs)
10. Temporal & Provenance
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from domain.base import BaseEntity, EntityType
from domain.shared import (
    ProvenanceAndConfidence,
    TemporalAndVersioning,
)

# ===========================================================================
# Sub-models
# ===========================================================================


class EarlyTerminationPenalty(BaseModel):
    """Early termination penalty details."""

    penalty_exists: bool | None = None
    penalty_description: str = ""
    penalty_amount: float | None = None
    currency: str = "USD"


class SLAEntry(BaseModel):
    """Service-level agreement entry."""

    sla_name: str = ""
    metric: str = ""
    target: str = ""
    measurement_method: str = ""
    penalty_for_breach: str = ""


class DataHandlingProvisions(BaseModel):
    """Data handling and privacy provisions (CISO-relevant)."""

    data_classification: list[str] = Field(default_factory=list)
    data_return_clause: bool | None = None
    data_destruction_clause: bool | None = None
    breach_notification_hours: float | None = None
    sub_processor_approval_required: bool | None = None


class InsuranceRequirements(BaseModel):
    """Insurance requirements in the contract."""

    cyber_insurance_required: bool | None = None
    minimum_coverage: float | None = None
    currency: str = "USD"
    verified: bool | None = None


class LiabilityCaps(BaseModel):
    """Liability caps and carve-outs."""

    liability_cap: float | None = None
    currency: str = "USD"
    liability_type: str = ""
    unlimited_liability_carve_outs: list[str] = Field(default_factory=list)


class IPProvisions(BaseModel):
    """Intellectual property provisions."""

    ip_ownership: str = ""
    work_product_ownership: str = ""
    license_grants: str = ""


class GoverningLaw(BaseModel):
    """Governing law and dispute resolution."""

    jurisdiction: str = ""
    dispute_resolution_mechanism: str = ""


class Amendment(BaseModel):
    """Contract amendment record."""

    amendment_id: str = ""
    amendment_date: str = ""
    description: str = ""
    financial_impact: float | None = None
    currency: str = "USD"


class AssociatedContract(BaseModel):
    """Cross-reference to a related contract."""

    contract_id: str = ""
    relationship: str = ""


# ===========================================================================
# Contract entity
# ===========================================================================


class Contract(BaseEntity):
    """A vendor/partner contract in the enterprise knowledge graph.

    Covers MSAs, SOWs, software licenses, SaaS subscriptions, supply
    agreements, NDAs, DPAs, and other commercial agreements.
    """

    ENTITY_TYPE: ClassVar[EntityType] = EntityType.CONTRACT
    entity_type: Literal[EntityType.CONTRACT] = EntityType.CONTRACT

    # --- Group 1: Identity ---
    contract_id: str = ""
    contract_type: str = ""
    contract_status: str = ""

    # --- Group 2: Parties & Ownership ---
    vendor_id: str = ""
    contract_owner: str = ""
    legal_owner: str = ""
    procurement_owner: str = ""
    contracting_org_unit: str = ""

    # --- Group 3: Financial Terms ---
    total_contract_value: float | None = None
    annual_value: float | None = None
    currency: str = "USD"
    payment_schedule: str = ""
    payment_terms: str = ""

    # --- Group 4: Duration & Renewal ---
    start_date: str = ""
    end_date: str = ""
    initial_term: str = ""
    current_term: str = ""
    auto_renewal: bool | None = None
    renewal_term: str = ""
    notice_period_days: int | None = None
    opt_out_deadline: str = ""
    renewal_cap_pct: float | None = None

    # --- Group 5: Termination ---
    termination_provisions: str = ""
    termination_for_convenience: bool | None = None
    termination_notice_days: int | None = None
    early_termination_penalty: EarlyTerminationPenalty | None = None

    # --- Group 6: SLAs ---
    sla_summary: list[SLAEntry] = Field(default_factory=list)

    # --- Group 7: Key Provisions ---
    data_handling_provisions: DataHandlingProvisions | None = None
    insurance_requirements: InsuranceRequirements | None = None
    liability_caps: LiabilityCaps | None = None
    ip_provisions: IPProvisions | None = None
    governing_law: GoverningLaw | None = None

    # --- Group 8: Amendments & Related ---
    amendments: list[Amendment] = Field(default_factory=list)
    associated_contracts: list[AssociatedContract] = Field(default_factory=list)

    # --- Group 9: Dependencies & Relationships ---
    with_vendor: str = ""
    covers_systems: list[str] = Field(default_factory=list)
    covers_data: list[str] = Field(default_factory=list)
    covers_products: list[str] = Field(default_factory=list)

    # --- Group 10: Temporal & Provenance ---
    temporal_and_versioning: TemporalAndVersioning = Field(
        default_factory=TemporalAndVersioning
    )
    provenance_and_confidence: ProvenanceAndConfidence = Field(
        default_factory=ProvenanceAndConfidence
    )
