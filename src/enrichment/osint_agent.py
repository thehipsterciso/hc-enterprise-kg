"""OSINT Research Agent — provides real-world grounding for enrichments.

This agent conducts open-source intelligence research to enrich entity data with
external reference information. In offline mode (default), it uses built-in reference
data from frameworks (NIST, ISO, MITRE, CIS). In online mode (future), it would use
web search to retrieve current threat intelligence, news, and regulatory data.

Usage:
    agent = OSINTResearchAgent(osint_enabled=False)  # Offline by default
    results = agent.research(entity, entity_context, EnrichmentTier.STANDARD)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from enrichment.base import SOURCE_VALIDITY_WINDOWS, EnrichmentTier, EntityContext, OSINTResults
from enrichment.osint.frameworks import (
    CIS_CONTROLS_V8,
    ISO_27001_CONTROLS,
    MITRE_ATTACK_TECHNIQUES,
    NIST_800_53_CONTROLS,
)


@dataclass
class SourceMetadata:
    """Metadata about an OSINT source for staleness tracking.

    Every piece of research data is accompanied by its source metadata
    so the adversarial validator can enforce staleness limits.
    """

    source_name: str  # e.g., "NIST SP 800-53 Rev 5"
    source_type: str  # e.g., "nist", "sec_filing", "web_search"
    publication_date: str  # ISO date when the source was published/last updated
    retrieval_date: str = ""  # ISO date when we retrieved this data
    validity_window_days: int = 365  # How long this source remains authoritative

    def __post_init__(self) -> None:
        if not self.retrieval_date:
            self.retrieval_date = datetime.now(UTC).isoformat()
        if self.source_type in SOURCE_VALIDITY_WINDOWS:
            self.validity_window_days = SOURCE_VALIDITY_WINDOWS[self.source_type]


@dataclass
class ResearchCache:
    """In-memory cache for research results to avoid duplicate lookups."""

    control_lookups: dict[str, dict[str, Any]] = field(default_factory=dict)
    technique_lookups: dict[str, dict[str, Any]] = field(default_factory=dict)
    regulation_lookups: dict[str, dict[str, Any]] = field(default_factory=dict)
    benchmark_lookups: dict[str, dict[str, Any]] = field(default_factory=dict)


class OSINTResearchAgent:
    """Provides real-world grounding for entity enrichments via OSINT research.

    This agent caches results to avoid redundant lookups. Built-in reference data
    is pre-loaded from frameworks.py. In future versions, can be extended to
    support online web search and threat intelligence feeds.

    Attributes:
        osint_enabled: If True, perform online lookups (future feature).
        cache: ResearchCache for caching lookup results.
    """

    def __init__(self, osint_enabled: bool = False):
        """Initialize the OSINT agent.

        Args:
            osint_enabled: If True, enable online OSINT (future). Default False.
        """
        self.osint_enabled = osint_enabled
        self.cache = ResearchCache()

    def research(
        self,
        entity: Any,  # BaseEntity
        entity_context: EntityContext,
        tier: EnrichmentTier = EnrichmentTier.STANDARD,
    ) -> OSINTResults:
        """Conduct OSINT research on an entity.

        Args:
            entity: The entity to research.
            entity_context: Full graph context for the entity.
            tier: Enrichment tier (BASIC, STANDARD, DEEP).

        Returns:
            OSINTResults containing research findings.
        """
        results = OSINTResults(
            entity_id=entity.id,
            entity_type=entity.entity_type,
        )

        entity_type_name = entity.entity_type.lower() if hasattr(entity, "entity_type") else ""

        # TIER 1: Local context only (no external research).
        if tier == EnrichmentTier.BASIC:
            return results

        # TIER 2+: Look up reference data based on entity type and content.
        if "control" in entity_type_name:
            self._research_control(entity, results, tier)
        elif "threat" in entity_type_name:
            self._research_threat(entity, results, tier)
        elif "regulation" in entity_type_name:
            self._research_regulation(entity, results, tier)
        elif "vulnerability" in entity_type_name:
            self._research_vulnerability(entity, results, tier)
        elif "system" in entity_type_name:
            self._research_system(entity, results, tier)
        elif "vendor" in entity_type_name:
            self._research_vendor(entity, results, tier)

        results.research_timestamp = datetime.now(UTC)
        return results

    def _research_control(
        self,
        entity: Any,
        results: OSINTResults,
        tier: EnrichmentTier,
    ) -> None:
        """Research a Control entity against frameworks.

        Each framework lookup now carries source metadata (publication date,
        source type, validity window) so the adversarial validator can enforce
        staleness limits downstream.
        """
        control_id = getattr(entity, "control_id", "") or getattr(entity, "name", "")

        # Look up in NIST, ISO, CIS — each with source metadata
        nist_match = self._lookup_nist_control(control_id)
        iso_match = self._lookup_iso_control(control_id)
        cis_match = self._lookup_cis_control(control_id)

        if nist_match:
            results.raw_data["nist_framework"] = nist_match
            results.raw_data["nist_source_metadata"] = SourceMetadata(
                source_name="NIST SP 800-53 Rev 5",
                source_type="nist",
                publication_date="2024-05-07",  # Rev 5.1.1 release date
            ).__dict__
            results.research_sources.append("NIST SP 800-53 Rev 5")

        if iso_match:
            results.raw_data["iso_framework"] = iso_match
            results.raw_data["iso_source_metadata"] = SourceMetadata(
                source_name="ISO/IEC 27001:2022",
                source_type="iso",
                publication_date="2022-10-25",
            ).__dict__
            results.research_sources.append("ISO/IEC 27001:2022")

        if cis_match:
            results.raw_data["cis_framework"] = cis_match
            results.raw_data["cis_source_metadata"] = SourceMetadata(
                source_name="CIS Controls v8.1",
                source_type="cis",
                publication_date="2024-06-25",
            ).__dict__
            results.research_sources.append("CIS Controls v8.1")

        # DEEP tier: Add regulatory references.
        if tier == EnrichmentTier.DEEP:
            description = getattr(entity, "description", "")
            if description:
                regulatory_findings = self._infer_regulatory_references(description)
                if regulatory_findings:
                    results.regulatory_findings = regulatory_findings
                    results.research_sources.extend(
                        [rf.get("source", "Unknown") for rf in regulatory_findings]
                    )

    def _research_threat(
        self,
        entity: Any,
        results: OSINTResults,
        tier: EnrichmentTier,
    ) -> None:
        """Research a Threat entity (MITRE ATT&CK)."""
        threat_name = getattr(entity, "name", "")

        # Look up MITRE techniques that match threat description.
        matching_techniques = self._match_mitre_techniques(threat_name)
        if matching_techniques:
            results.threat_intel = matching_techniques
            results.raw_data["mitre_source_metadata"] = SourceMetadata(
                source_name="MITRE ATT&CK v14",
                source_type="mitre",
                publication_date="2024-10-31",  # ATT&CK v14 release
            ).__dict__
            results.research_sources.append("MITRE ATT&CK v14")

        # DEEP tier: Add tactical grouping.
        if tier == EnrichmentTier.DEEP:
            tactics = set()
            for technique in matching_techniques:
                tactic = technique.get("tactic")
                if tactic:
                    tactics.add(tactic)
            if tactics:
                results.raw_data["tactics"] = list(tactics)

    def _research_regulation(
        self,
        entity: Any,
        results: OSINTResults,
        tier: EnrichmentTier,
    ) -> None:
        """Research a Regulation entity."""
        reg_name = getattr(entity, "name", "")
        reg_id = getattr(entity, "regulation_id", "")

        # Look up regulatory requirements.
        requirements = self._lookup_regulation_requirements(reg_name or reg_id)
        if requirements:
            results.regulatory_findings = [requirements]
            source = requirements.get("source", "Unknown")
            results.research_sources.append(source)

            # Attach source metadata based on regulation type
            reg_lower = (reg_name or reg_id or "").lower()
            if "gdpr" in reg_lower:
                pub_date = "2016-04-27"  # GDPR adopted
            elif "hipaa" in reg_lower:
                pub_date = "1996-08-21"  # HIPAA enacted
            elif "sox" in reg_lower or "sarbanes" in reg_lower:
                pub_date = "2002-07-30"  # SOX enacted
            else:
                pub_date = "2020-01-01"  # Conservative default for unknown

            results.raw_data["regulation_source_metadata"] = SourceMetadata(
                source_name=source,
                source_type="regulatory_text",
                publication_date=pub_date,
            ).__dict__

    def _research_vulnerability(
        self,
        entity: Any,
        results: OSINTResults,
        tier: EnrichmentTier,
    ) -> None:
        """Research a Vulnerability entity."""
        getattr(entity, "name", "")
        cve = getattr(entity, "cve_id", "")

        # In future: Look up CVE details from NVD API.
        # For now, add a placeholder.
        if cve:
            results.raw_data["cve_reference"] = f"https://nvd.nist.gov/vuln/detail/{cve}"
            results.research_sources.append("NVD (future)")

    def _research_system(
        self,
        entity: Any,
        results: OSINTResults,
        tier: EnrichmentTier,
    ) -> None:
        """Research a System entity for benchmarks."""
        getattr(entity, "system_type", "")
        profile = getattr(entity, "profile", "tech")

        benchmarks = self._get_industry_benchmarks("system", profile)
        if benchmarks:
            results.raw_data["industry_benchmarks"] = benchmarks
            results.research_sources.append("Industry Benchmarks")

    def _research_vendor(
        self,
        entity: Any,
        results: OSINTResults,
        tier: EnrichmentTier,
    ) -> None:
        """Research a Vendor entity."""
        vendor_name = getattr(entity, "name", "")

        # In future: Conduct web search for vendor news, reputation, regulatory issues.
        # For now, placeholder.
        results.raw_data["vendor_research_pending"] = f"Future: Research {vendor_name}"
        results.research_sources.append("Web Search (future)")

    # --- Built-in reference data lookups ---

    def _lookup_nist_control(self, control_id: str) -> dict[str, Any] | None:
        """Look up a NIST SP 800-53 control by ID.

        Args:
            control_id: Control ID (e.g., "AC-2", "AC-2.1").

        Returns:
            Control details dict, or None if not found.
        """
        # Check cache first.
        if control_id in self.cache.control_lookups:
            return self.cache.control_lookups[control_id]

        # Normalize to base control (e.g., "AC-2.1" -> "AC-2").
        base_id = control_id.split(".")[0] if "." in control_id else control_id

        result = NIST_800_53_CONTROLS.get(base_id)
        if result:
            self.cache.control_lookups[control_id] = result

        return result

    def _lookup_iso_control(self, control_id: str) -> dict[str, Any] | None:
        """Look up an ISO 27001 control by ID."""
        if control_id in self.cache.control_lookups:
            return self.cache.control_lookups[control_id]

        result = ISO_27001_CONTROLS.get(control_id)
        if result:
            self.cache.control_lookups[control_id] = result

        return result

    def _lookup_cis_control(self, control_id: str) -> dict[str, Any] | None:
        """Look up a CIS Controls v8 control by ID."""
        if control_id in self.cache.control_lookups:
            return self.cache.control_lookups[control_id]

        result = CIS_CONTROLS_V8.get(control_id)
        if result:
            self.cache.control_lookups[control_id] = result

        return result

    def _match_mitre_techniques(self, description: str) -> list[dict[str, Any]]:
        """Match MITRE ATT&CK techniques against a threat description.

        Args:
            description: Threat description or name.

        Returns:
            List of matching technique dicts.
        """
        matches = []
        search_lower = description.lower()

        for _technique_id, technique_data in MITRE_ATTACK_TECHNIQUES.items():
            technique_name = technique_data.get("technique", "").lower()
            if technique_name in search_lower or search_lower in technique_name:
                matches.append(technique_data)

        return matches

    def _lookup_regulation_requirements(self, regulation_name: str) -> dict[str, Any]:
        """Look up requirements for a regulation.

        Args:
            regulation_name: Name or ID of the regulation.

        Returns:
            Requirements dict with key fields and source.
        """
        if regulation_name in self.cache.regulation_lookups:
            return self.cache.regulation_lookups[regulation_name]

        # Simple matching against common regulations.
        reg_lower = regulation_name.lower()

        if "gdpr" in reg_lower:
            result = {
                "regulation": "GDPR",
                "key_requirements": [
                    "Data protection by design",
                    "Consent management",
                    "Data subject rights",
                    "Data breach notification (72h)",
                    "DPIA for high-risk processing",
                ],
                "jurisdiction": "EU",
                "source": "EU Regulation 2016/679",
            }
        elif "hipaa" in reg_lower:
            result = {
                "regulation": "HIPAA",
                "key_requirements": [
                    "Administrative safeguards",
                    "Physical safeguards",
                    "Technical safeguards",
                    "Breach notification (60d)",
                    "Privacy and security rules",
                ],
                "jurisdiction": "US",
                "source": "45 CFR Parts 160 and 164",
            }
        elif "sox" in reg_lower or "sarbanes" in reg_lower:
            result = {
                "regulation": "Sarbanes-Oxley",
                "key_requirements": [
                    "IT general controls",
                    "Financial reporting controls",
                    "Audit committee oversight",
                    "Internal audit function",
                    "Change management",
                ],
                "jurisdiction": "US",
                "source": "15 U.S.C. § 7201 et seq.",
            }
        else:
            result = {
                "regulation": regulation_name,
                "key_requirements": ["Unknown regulation"],
                "jurisdiction": "Unknown",
                "source": "Manual research required",
            }

        self.cache.regulation_lookups[regulation_name] = result
        return result

    def _get_industry_benchmarks(self, entity_type: str, profile: str) -> dict[str, Any]:
        """Get industry benchmarks for a given entity type and profile.

        Args:
            entity_type: Type of entity (e.g., "system", "person", "vendor").
            profile: Profile type (e.g., "tech", "financial", "healthcare").

        Returns:
            Benchmarks dict with key metrics.
        """
        cache_key = f"{entity_type}_{profile}"
        if cache_key in self.cache.benchmark_lookups:
            return self.cache.benchmark_lookups[cache_key]

        benchmarks = {}

        if entity_type == "system":
            if profile == "tech":
                benchmarks = {
                    "avg_annual_cost": 75000,
                    "median_criticality": "high",
                    "availability_target": "99.95%",
                }
            elif profile == "financial":
                benchmarks = {
                    "avg_annual_cost": 250000,
                    "median_criticality": "critical",
                    "availability_target": "99.99%",
                }
        elif entity_type == "person":
            if profile == "tech":
                benchmarks = {
                    "avg_salary_usd": 145000,
                    "certification_pct": 65,
                    "avg_tenure_years": 4.2,
                }
            elif profile == "financial":
                benchmarks = {
                    "avg_salary_usd": 165000,
                    "certification_pct": 75,
                    "avg_tenure_years": 5.8,
                }

        self.cache.benchmark_lookups[cache_key] = benchmarks
        return benchmarks

    def _infer_regulatory_references(self, description: str) -> list[dict[str, Any]]:
        """Infer regulatory references from entity description.

        Args:
            description: Entity description text.

        Returns:
            List of inferred regulatory findings.
        """
        findings = []
        desc_lower = description.lower()

        if "gdpr" in desc_lower:
            findings.append(
                {
                    "regulation": "GDPR",
                    "relevance": "mentioned",
                    "source": "Text Analysis",
                }
            )
        if "hipaa" in desc_lower:
            findings.append(
                {
                    "regulation": "HIPAA",
                    "relevance": "mentioned",
                    "source": "Text Analysis",
                }
            )
        if "pci" in desc_lower:
            findings.append(
                {
                    "regulation": "PCI DSS",
                    "relevance": "mentioned",
                    "source": "Text Analysis",
                }
            )
        if "sox" in desc_lower or "sarbanes" in desc_lower:
            findings.append(
                {
                    "regulation": "Sarbanes-Oxley",
                    "relevance": "mentioned",
                    "source": "Text Analysis",
                }
            )

        return findings
