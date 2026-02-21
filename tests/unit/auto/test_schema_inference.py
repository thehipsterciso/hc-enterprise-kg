"""Tests for schema inference across all 30 entity types."""

from __future__ import annotations

from auto.schema_inference import infer_entity_type, infer_relationships
from domain.base import EntityType


class TestInferEntityTypeOriginal:
    """Regression tests for the original 11 entity types."""

    def test_person(self) -> None:
        cols = ["first_name", "last_name", "email", "hire_date"]
        assert infer_entity_type(cols) == EntityType.PERSON

    def test_department(self) -> None:
        cols = ["department", "dept_code", "business_unit"]
        assert infer_entity_type(cols) == EntityType.DEPARTMENT

    def test_system(self) -> None:
        cols = ["hostname", "ip_address", "os", "port"]
        assert infer_entity_type(cols) == EntityType.SYSTEM

    def test_network(self) -> None:
        cols = ["cidr", "subnet", "vlan", "gateway"]
        assert infer_entity_type(cols) == EntityType.NETWORK

    def test_vulnerability(self) -> None:
        cols = ["cve", "cvss", "severity", "exploit"]
        assert infer_entity_type(cols) == EntityType.VULNERABILITY

    def test_vendor(self) -> None:
        cols = ["vendor", "supplier", "sla"]
        assert infer_entity_type(cols) == EntityType.VENDOR

    def test_data_asset(self) -> None:
        cols = ["data_asset", "classification", "retention", "encryption"]
        assert infer_entity_type(cols) == EntityType.DATA_ASSET

    def test_policy(self) -> None:
        cols = ["policy", "policy_type", "policy_status", "framework"]
        assert infer_entity_type(cols) == EntityType.POLICY

    def test_location(self) -> None:
        cols = ["location", "address", "city", "country"]
        assert infer_entity_type(cols) == EntityType.LOCATION

    def test_threat_actor(self) -> None:
        cols = ["threat_actor", "apt", "adversary", "campaign"]
        assert infer_entity_type(cols) == EntityType.THREAT_ACTOR

    def test_incident(self) -> None:
        cols = ["incident", "breach", "detection", "forensic"]
        assert infer_entity_type(cols) == EntityType.INCIDENT


class TestInferEntityTypeEnterprise:
    """Tests for the 19 enterprise entity types."""

    def test_role(self) -> None:
        cols = ["role_type", "role_family", "access_level", "permissions"]
        assert infer_entity_type(cols) == EntityType.ROLE

    def test_regulation(self) -> None:
        cols = ["regulation_id", "regulation_category", "issuing_body"]
        assert infer_entity_type(cols) == EntityType.REGULATION

    def test_control(self) -> None:
        cols = ["control_id", "control_type", "control_domain", "control_status"]
        assert infer_entity_type(cols) == EntityType.CONTROL

    def test_risk(self) -> None:
        cols = ["risk_id", "risk_category", "risk_level", "risk_owner"]
        assert infer_entity_type(cols) == EntityType.RISK

    def test_threat(self) -> None:
        cols = ["threat_id", "threat_category", "threat_group", "threat_source"]
        assert infer_entity_type(cols) == EntityType.THREAT

    def test_integration(self) -> None:
        cols = ["integration_id", "integration_type", "protocol", "middleware"]
        assert infer_entity_type(cols) == EntityType.INTEGRATION

    def test_data_domain(self) -> None:
        cols = ["domain_id", "domain_type", "domain_owner", "data_domain"]
        assert infer_entity_type(cols) == EntityType.DATA_DOMAIN

    def test_data_flow(self) -> None:
        cols = ["flow_id", "flow_type", "transfer_method", "data_flow"]
        assert infer_entity_type(cols) == EntityType.DATA_FLOW

    def test_organizational_unit(self) -> None:
        cols = ["unit_id", "unit_type", "operating_model", "org_unit"]
        assert infer_entity_type(cols) == EntityType.ORGANIZATIONAL_UNIT

    def test_business_capability(self) -> None:
        cols = ["capability_id", "capability_level", "maturity_level"]
        assert infer_entity_type(cols) == EntityType.BUSINESS_CAPABILITY

    def test_site(self) -> None:
        cols = ["site_id", "site_type", "site_status", "building"]
        assert infer_entity_type(cols) == EntityType.SITE

    def test_geography(self) -> None:
        cols = ["geography_id", "geography_type", "region_code"]
        assert infer_entity_type(cols) == EntityType.GEOGRAPHY

    def test_jurisdiction(self) -> None:
        cols = ["jurisdiction_id", "jurisdiction_type", "governing_body"]
        assert infer_entity_type(cols) == EntityType.JURISDICTION

    def test_product_portfolio(self) -> None:
        cols = ["portfolio_id", "portfolio_type", "product_portfolio"]
        assert infer_entity_type(cols) == EntityType.PRODUCT_PORTFOLIO

    def test_product(self) -> None:
        cols = ["product_id", "product_type", "lifecycle_stage"]
        assert infer_entity_type(cols) == EntityType.PRODUCT

    def test_market_segment(self) -> None:
        cols = ["segment_id", "segment_type", "market_segment"]
        assert infer_entity_type(cols) == EntityType.MARKET_SEGMENT

    def test_customer(self) -> None:
        cols = ["customer_id", "customer_type", "account_tier"]
        assert infer_entity_type(cols) == EntityType.CUSTOMER

    def test_contract(self) -> None:
        cols = ["contract_id", "contract_type", "contract_status", "contract_value"]
        assert infer_entity_type(cols) == EntityType.CONTRACT

    def test_initiative(self) -> None:
        cols = ["initiative_id", "initiative_type", "executive_sponsor"]
        assert infer_entity_type(cols) == EntityType.INITIATIVE


class TestInferEntityTypeEdgeCases:
    """Edge cases and ambiguity tests."""

    def test_no_match_returns_none(self) -> None:
        cols = ["col_a", "col_b", "col_c"]
        assert infer_entity_type(cols) is None

    def test_empty_columns_returns_none(self) -> None:
        assert infer_entity_type([]) is None

    def test_highest_score_wins(self) -> None:
        # 3 person signals vs 1 system signal
        cols = ["first_name", "last_name", "email", "hostname"]
        assert infer_entity_type(cols) == EntityType.PERSON

    def test_policy_no_longer_matches_control(self) -> None:
        # "control" was removed from POLICY patterns
        cols = ["control_id", "control_type", "control_domain"]
        result = infer_entity_type(cols)
        assert result == EntityType.CONTROL
        assert result != EntityType.POLICY

    def test_policy_no_longer_matches_regulation(self) -> None:
        cols = ["regulation_id", "regulation_category", "issuing_body"]
        result = infer_entity_type(cols)
        assert result == EntityType.REGULATION
        assert result != EntityType.POLICY

    def test_location_no_longer_matches_site(self) -> None:
        # "site" was moved from LOCATION to SITE type
        cols = ["site_id", "site_type", "site_status"]
        result = infer_entity_type(cols)
        assert result == EntityType.SITE


class TestInferRelationships:
    """Tests for relationship column detection."""

    def test_original_patterns(self) -> None:
        cols = ["name", "department_id", "manager_id", "system_id"]
        rels = infer_relationships(cols)
        hints = {r[1] for r in rels}
        assert "entity_to_department" in hints
        assert "person_to_manager" in hints
        assert "entity_to_system" in hints

    def test_new_enterprise_patterns(self) -> None:
        cols = ["regulation_id", "control_id", "risk_id", "contract_id"]
        rels = infer_relationships(cols)
        hints = {r[1] for r in rels}
        assert "entity_to_regulation" in hints
        assert "entity_to_control" in hints
        assert "entity_to_risk" in hints
        assert "entity_to_contract" in hints

    def test_initiative_product_customer_patterns(self) -> None:
        cols = ["initiative_id", "product_id", "customer_id"]
        rels = infer_relationships(cols)
        hints = {r[1] for r in rels}
        assert "entity_to_initiative" in hints
        assert "entity_to_product" in hints
        assert "entity_to_customer" in hints

    def test_capability_portfolio_patterns(self) -> None:
        cols = ["capability_id", "portfolio_id"]
        rels = infer_relationships(cols)
        hints = {r[1] for r in rels}
        assert "entity_to_capability" in hints
        assert "entity_to_portfolio" in hints

    def test_no_matches(self) -> None:
        cols = ["col_a", "col_b"]
        assert infer_relationships(cols) == []
