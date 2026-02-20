"""Visual theme constants for analytics charts.

Reuses ENTITY_COLORS from the interactive visualizer for consistency
across all visualization outputs.
"""

from __future__ import annotations

# Entity type colors — matches src/cli/visualize_cmd.py for consistency
ENTITY_COLORS: dict[str, str] = {
    # v0.1 original types
    "person": "#4E79A7",
    "department": "#F28E2B",
    "role": "#E15759",
    "system": "#76B7B2",
    "network": "#59A14F",
    "data_asset": "#EDC948",
    "policy": "#B07AA1",
    "vendor": "#FF9DA7",
    "location": "#9C755F",
    "vulnerability": "#BAB0AC",
    "threat_actor": "#D37295",
    "incident": "#FABFD2",
    # Enterprise ontology types
    "regulation": "#A0CBE8",
    "control": "#FFBE7D",
    "risk": "#8CD17D",
    "threat": "#B6992D",
    "integration": "#499894",
    "data_domain": "#86BCB6",
    "data_flow": "#F1CE63",
    "organizational_unit": "#E6A0C4",
    "business_capability": "#D4A6C8",
    "site": "#C49C94",
    "geography": "#DBDB8D",
    "jurisdiction": "#9EDAE5",
    "product_portfolio": "#AEC7E8",
    "product": "#98DF8A",
    "market_segment": "#C5B0D5",
    "customer": "#C7C7C7",
    "contract": "#FFBB78",
    "initiative": "#FF9896",
}

# Profile colors for multi-profile comparison charts
PROFILE_COLORS: dict[str, str] = {
    "tech": "#4E79A7",
    "financial": "#F28E2B",
    "healthcare": "#59A14F",
}

# Entity types grouped by generation layer for readable scaling charts
ENTITY_TYPE_GROUPS: dict[str, list[str]] = {
    "People & Org": ["person", "department", "role", "organizational_unit"],
    "Core Infrastructure": ["system", "network", "data_asset", "integration"],
    "Security": ["vulnerability", "threat_actor", "incident", "threat"],
    "Governance": ["policy", "regulation", "control", "risk"],
    "Data": ["data_domain", "data_flow"],
    "Locations": ["location", "site", "geography", "jurisdiction"],
    "Commercial": [
        "vendor",
        "customer",
        "contract",
        "product",
        "product_portfolio",
        "market_segment",
    ],
    "Strategy": ["business_capability", "initiative"],
}

# Group colors for scaling curves
GROUP_COLORS: dict[str, str] = {
    "People & Org": "#4E79A7",
    "Core Infrastructure": "#76B7B2",
    "Security": "#E15759",
    "Governance": "#B07AA1",
    "Data": "#EDC948",
    "Locations": "#9C755F",
    "Commercial": "#FF9DA7",
    "Strategy": "#59A14F",
}

# QualityReport dimension labels (human-readable)
QUALITY_DIMENSION_LABELS: dict[str, str] = {
    "risk_math_consistency": "Risk Math",
    "description_quality": "Description Quality",
    "tech_stack_coherence": "Tech Coherence",
    "field_correlation_score": "Field Correlation",
    "encryption_classification_consistency": "Encryption/Classification",
}

# Standard figure sizes
FIGURE_SIZE_STANDARD: tuple[int, int] = (12, 7)
FIGURE_SIZE_WIDE: tuple[int, int] = (14, 7)
FIGURE_SIZE_RADAR: tuple[int, int] = (8, 8)

# Font sizes
FONT_TITLE: int = 14
FONT_LABEL: int = 11
FONT_TICK: int = 9
