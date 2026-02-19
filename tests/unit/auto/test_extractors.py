"""Tests for auto extractors."""

from hc_enterprise_kg.auto.extractors.rule_based import RuleBasedExtractor
from hc_enterprise_kg.domain.base import EntityType


class TestRuleBasedExtractor:
    def test_extract_emails(self):
        text = "Contact alice@example.com and bob@acme.com for details."
        extractor = RuleBasedExtractor()
        result = extractor.extract(text)
        emails = [e for e in result.entities if e.entity_type == EntityType.PERSON]
        assert len(emails) == 2

    def test_extract_ips(self):
        text = "Server at 10.0.1.50 is down. Check 192.168.1.1 as well."
        extractor = RuleBasedExtractor()
        result = extractor.extract(text)
        systems = [e for e in result.entities if e.entity_type == EntityType.SYSTEM]
        assert len(systems) == 2

    def test_extract_cves(self):
        text = "Affected by CVE-2024-12345 and CVE-2023-98765."
        extractor = RuleBasedExtractor()
        result = extractor.extract(text)
        vulns = [e for e in result.entities if e.entity_type == EntityType.VULNERABILITY]
        assert len(vulns) == 2
        assert any(v.cve_id == "CVE-2024-12345" for v in vulns)

    def test_no_duplicates(self):
        text = "Contact alice@example.com. Repeat: alice@example.com"
        extractor = RuleBasedExtractor()
        result = extractor.extract(text)
        assert len(result.entities) == 1

    def test_can_handle(self):
        extractor = RuleBasedExtractor()
        assert extractor.can_handle("some text") is True
        assert extractor.can_handle("") is False
        assert extractor.can_handle(123) is False

    def test_confidence_set(self):
        text = "Contact alice@example.com"
        extractor = RuleBasedExtractor()
        result = extractor.extract(text)
        assert result.entities[0].metadata.get("_confidence") is not None
