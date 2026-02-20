"""Stub entity classes for enterprise ontology types not yet fully implemented.

Each stub is a minimal BaseEntity subclass with the correct ENTITY_TYPE.
As each layer branch is built, the stub is replaced by a full implementation
in its own file (e.g., regulation.py, control.py, etc.) and removed from
this file.

Stubs accept arbitrary extra fields via BaseEntity's extra="allow" config,
so JSON data with full attribute sets can be ingested even before the
detailed entity class is built.
"""

from __future__ import annotations

# --- L01: Compliance & Governance ---
# Regulation, Control, Risk, Threat — replaced by full implementations in L01.
# See: regulation.py, control.py, risk.py, threat.py

# --- L02: Technology & Systems ---
# Integration — replaced by full implementation in L02.
# See: integration.py (System extended in system.py)

# --- L03: Data Assets ---
# DataDomain, DataFlow — replaced by full implementations in L03.
# See: data_domain.py, data_flow.py (DataAsset extended in data_asset.py)

# --- L04: Organization ---
# OrganizationalUnit — replaced by full implementation in L04.
# See: organizational_unit.py

# --- L06: Business Capabilities ---
# BusinessCapability — replaced by full implementation in L06.
# See: business_capability.py

# --- L07: Locations & Facilities ---
# Site, Geography, Jurisdiction — replaced by full implementations in L07.
# See: site.py, geography.py, jurisdiction.py

# --- L08: Products & Services ---
# ProductPortfolio, Product — replaced by full implementations in L08.
# See: product_portfolio.py, product.py

# --- L09: Customers & Markets ---
# MarketSegment, Customer — replaced by full implementations in L09.
# See: market_segment.py, customer.py

# --- L10: Vendors & Partners ---
# Contract — replaced by full implementation in L10. Vendor extended in vendor.py.
# See: contract.py

# --- L11: Strategic Initiatives ---
# Initiative — replaced by full implementation in L11.
# See: initiative.py

# All stubs have been replaced by full implementations.
