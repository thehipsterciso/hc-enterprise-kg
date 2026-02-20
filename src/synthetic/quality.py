"""Quality scoring module for synthetic data generation.

Evaluates semantic coherence, field correlation, and data quality
of generated entities. Returns a QualityReport with per-metric scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from domain.base import EntityType
from synthetic.generators.enterprise import RISK_MATRIX

if TYPE_CHECKING:
    from synthetic.base import GenerationContext


@dataclass
class QualityReport:
    """Results of a quality assessment on generated synthetic data."""

    overall_score: float = 0.0
    risk_math_consistency: float = 0.0
    description_quality: float = 0.0
    tech_stack_coherence: float = 0.0
    field_correlation_score: float = 0.0
    encryption_classification_consistency: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary of the quality report."""
        lines = [
            f"Overall Score: {self.overall_score:.2f}",
            f"  Risk Math Consistency:     {self.risk_math_consistency:.2f}",
            f"  Description Quality:       {self.description_quality:.2f}",
            f"  Tech Stack Coherence:      {self.tech_stack_coherence:.2f}",
            f"  Field Correlation:         {self.field_correlation_score:.2f}",
            f"  Encryption/Classification: {self.encryption_classification_consistency:.2f}",
        ]
        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings[:5]:
                lines.append(f"    - {w}")
        return "\n".join(lines)


# Patterns that indicate lorem ipsum / faker junk
LOREM_PATTERNS = [
    re.compile(r"\b(lorem|ipsum|dolor|sit amet|consectetur)\b", re.IGNORECASE),
    re.compile(r"^[A-Z][a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+\.$"),
]


def _is_lorem(text: str) -> bool:
    """Check if text looks like faker.sentence() or lorem ipsum."""
    return any(pattern.search(text) for pattern in LOREM_PATTERNS)


def assess_quality(context: GenerationContext) -> QualityReport:
    """Run all quality checks against generated entities in context."""
    report = QualityReport()

    scores = []

    # 1. Risk math consistency: risk_level = f(likelihood, impact)
    risk_score = _check_risk_math(context, report)
    report.risk_math_consistency = risk_score
    scores.append(risk_score)

    # 2. Description quality: no lorem ipsum / faker junk
    desc_score = _check_description_quality(context, report)
    report.description_quality = desc_score
    scores.append(desc_score)

    # 3. Tech stack coherence (systems)
    tech_score = _check_tech_stack_coherence(context, report)
    report.tech_stack_coherence = tech_score
    scores.append(tech_score)

    # 4. Field correlation checks
    corr_score = _check_field_correlations(context, report)
    report.field_correlation_score = corr_score
    scores.append(corr_score)

    # 5. Encryption ↔ classification consistency
    enc_score = _check_encryption_classification(context, report)
    report.encryption_classification_consistency = enc_score
    scores.append(enc_score)

    report.overall_score = sum(scores) / len(scores) if scores else 0.0
    return report


def _check_risk_math(context: GenerationContext, report: QualityReport) -> float:
    """Check that risk_level = RISK_MATRIX[likelihood][impact]."""
    risks = context.get_entities(EntityType.RISK)
    if not risks:
        return 1.0

    correct = 0
    for risk in risks:
        likelihood = getattr(risk, "inherent_likelihood", None)
        impact = getattr(risk, "inherent_impact", None)
        level = getattr(risk, "inherent_risk_level", None)
        if likelihood and impact and level:
            expected = RISK_MATRIX.get(likelihood, {}).get(impact)
            if expected == level:
                correct += 1
            else:
                report.warnings.append(
                    f"Risk '{risk.name}': level={level} but "
                    f"expected={expected} from {likelihood}×{impact}"
                )
        else:
            correct += 1  # Missing fields are not a math error

    return correct / len(risks)


def _check_description_quality(context: GenerationContext, report: QualityReport) -> float:
    """Check that descriptions are not lorem ipsum or faker junk."""
    entity_types = [
        EntityType.PERSON, EntityType.SYSTEM, EntityType.DATA_ASSET,
        EntityType.VENDOR, EntityType.INCIDENT, EntityType.VULNERABILITY,
        EntityType.RISK, EntityType.THREAT, EntityType.CONTROL,
        EntityType.INTEGRATION, EntityType.DATA_FLOW, EntityType.CUSTOMER,
        EntityType.CONTRACT, EntityType.INITIATIVE, EntityType.POLICY,
    ]

    total = 0
    good = 0
    for etype in entity_types:
        entities = context.get_entities(etype)
        for entity in entities:
            desc = getattr(entity, "description", None)
            if desc:
                total += 1
                if not _is_lorem(desc):
                    good += 1
                else:
                    report.warnings.append(
                        f"{etype.value} '{entity.name}': lorem ipsum description"
                    )

    return good / total if total > 0 else 1.0


def _check_tech_stack_coherence(context: GenerationContext, report: QualityReport) -> float:
    """Check that system tech stacks are coherent with system type."""
    systems = context.get_entities(EntityType.SYSTEM)
    if not systems:
        return 1.0

    # Incoherent combos: appliance/workstation shouldn't have web frameworks
    web_frameworks = {"django", "rails", "react", "express", "spring", "flask"}
    appliance_types = {"appliance"}

    total = len(systems)
    coherent = 0
    for system in systems:
        sys_type = getattr(system, "system_type", "")
        techs = set(getattr(system, "technologies", []))
        if sys_type in appliance_types and techs & web_frameworks:
            report.warnings.append(
                f"System '{system.name}': {sys_type} with web framework {techs & web_frameworks}"
            )
        else:
            coherent += 1

    return coherent / total


def _check_field_correlations(context: GenerationContext, report: QualityReport) -> float:
    """Check various field correlations across entity types."""
    checks = 0
    passes = 0

    # Risk: residual ≤ inherent
    risk_level_order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    risks = context.get_entities(EntityType.RISK)
    for risk in risks:
        inh = getattr(risk, "inherent_risk_level", None)
        res = getattr(risk, "residual_risk_level", None)
        if inh and res:
            checks += 1
            if risk_level_order.get(res, 0) <= risk_level_order.get(inh, 3):
                passes += 1
            else:
                report.warnings.append(
                    f"Risk '{risk.name}': residual ({res}) > inherent ({inh})"
                )

    # Vulnerability: patch_available correlates with status
    vulns = context.get_entities(EntityType.VULNERABILITY)
    for vuln in vulns:
        patch = getattr(vuln, "patch_available", None)
        status = getattr(vuln, "status", None)
        if patch is not None and status:
            checks += 1
            # If patch available, status should skew toward mitigated/resolved
            if (patch and status in ("mitigated", "resolved")) or (
                not patch and status in ("open", "accepted")
            ):
                passes += 1
            else:
                passes += 0.5  # Partial credit — not strictly wrong

    # Site: data_center should have restricted security
    sites = context.get_entities(EntityType.SITE)
    for site in sites:
        site_type = getattr(site, "site_type", "")
        security = getattr(site, "physical_security_tier", "")
        if site_type == "Data Center":
            checks += 1
            if security == "Restricted":
                passes += 1
            else:
                report.warnings.append(
                    f"Site '{site.name}': Data Center with {security} security"
                )

    return passes / checks if checks > 0 else 1.0


def _check_encryption_classification(
    context: GenerationContext, report: QualityReport
) -> float:
    """Check that data flows with restricted/confidential data are encrypted."""
    flows = context.get_entities(EntityType.DATA_FLOW)
    if not flows:
        return 1.0

    total = 0
    encrypted = 0
    for flow in flows:
        classification = getattr(flow, "data_classification", "")
        is_encrypted = getattr(flow, "encryption_in_transit", False)
        if classification in ("Restricted", "Confidential"):
            total += 1
            if is_encrypted:
                encrypted += 1
            else:
                report.warnings.append(
                    f"DataFlow '{flow.name}': {classification} data not encrypted in transit"
                )

    return encrypted / total if total > 0 else 1.0
