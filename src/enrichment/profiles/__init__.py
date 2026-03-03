"""Enrichment profiles — industry-specific enrichment configuration."""

from __future__ import annotations

from enrichment.profiles.base import EnrichmentProfile
from enrichment.profiles.financial import FinancialEnrichmentProfile
from enrichment.profiles.healthcare import HealthcareEnrichmentProfile
from enrichment.profiles.tech import TechEnrichmentProfile

__all__ = [
    "EnrichmentProfile",
    "TechEnrichmentProfile",
    "FinancialEnrichmentProfile",
    "HealthcareEnrichmentProfile",
]
