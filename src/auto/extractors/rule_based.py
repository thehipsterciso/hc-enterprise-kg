"""Rule-based entity extraction using regex patterns."""

from __future__ import annotations

import re
import uuid
from typing import Any

from auto.base import ExtractionResult
from auto.confidence import ConfidenceSource, compute_confidence
from auto.extractors.base import AbstractExtractor
from domain.base import BaseEntity, EntityType
from domain.entities.person import Person
from domain.entities.system import System
from domain.entities.vulnerability import Vulnerability

# Compiled patterns for entity detection
PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "cve": re.compile(r"\bCVE-\d{4}-\d{4,7}\b"),
    "hostname": re.compile(r"\b[a-z][a-z0-9-]*\.(local|internal|corp|com|net|org)\b", re.IGNORECASE),
    "cidr": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b"),
}


class RuleBasedExtractor(AbstractExtractor):
    """Extracts entities from text using regex patterns.

    Detects: email addresses (→ Person), IP addresses (→ System),
    CVE IDs (→ Vulnerability), hostnames (→ System), CIDR ranges (→ Network).
    """

    def can_handle(self, data: Any) -> bool:
        return isinstance(data, str) and len(data) > 0

    def extract(self, data: Any, **kwargs: Any) -> ExtractionResult:
        if not isinstance(data, str):
            return ExtractionResult(source="rule_based", errors=["Data must be a string"])

        text = data
        entities: list[BaseEntity] = []
        seen: set[str] = set()
        confidence = compute_confidence(ConfidenceSource.RULE_BASED)

        # Extract emails → Person entities
        for match in PATTERNS["email"].finditer(text):
            email = match.group()
            if email in seen:
                continue
            seen.add(email)
            seen.add(email.split("@")[1])  # Prevent domain from matching as hostname
            local = email.split("@")[0]
            parts = re.split(r"[._-]", local)
            first = parts[0].title() if parts else "Unknown"
            last = parts[1].title() if len(parts) > 1 else ""

            entities.append(
                Person(
                    name=f"{first} {last}".strip(),
                    first_name=first,
                    last_name=last,
                    email=email,
                    metadata={"_confidence": confidence, "_source": "rule_based"},
                )
            )

        # Extract IPs → System entities
        for match in PATTERNS["ipv4"].finditer(text):
            ip = match.group()
            if ip in seen:
                continue
            seen.add(ip)
            entities.append(
                System(
                    name=f"System at {ip}",
                    ip_address=ip,
                    system_type="unknown",
                    metadata={"_confidence": confidence, "_source": "rule_based"},
                )
            )

        # Extract CVEs → Vulnerability entities
        for match in PATTERNS["cve"].finditer(text):
            cve = match.group()
            if cve in seen:
                continue
            seen.add(cve)
            entities.append(
                Vulnerability(
                    name=cve,
                    cve_id=cve,
                    metadata={"_confidence": confidence, "_source": "rule_based"},
                )
            )

        # Extract hostnames → System entities
        for match in PATTERNS["hostname"].finditer(text):
            hostname = match.group()
            if hostname in seen:
                continue
            seen.add(hostname)
            entities.append(
                System(
                    name=hostname,
                    hostname=hostname,
                    system_type="unknown",
                    metadata={"_confidence": confidence, "_source": "rule_based"},
                )
            )

        return ExtractionResult(entities=entities, source="rule_based")
