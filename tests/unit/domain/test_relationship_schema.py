"""Tests for widened RELATIONSHIP_SCHEMA domain/range constraints.

Validates that the schema accepts real-world entity combinations needed
for OSINT-derived knowledge graphs (issue #243).
"""

from __future__ import annotations

import pytest

from domain.base import EntityType, RelationshipType
from domain.relationship_schema import RELATIONSHIP_SCHEMA, validate_relationship


class TestWidenedSubjectTo:
    """subject_to now accepts Data_Domain, Customer, Department as sources
    and Policy, Control as targets."""

    @pytest.mark.parametrize(
        "source_type",
        [
            EntityType.DATA_DOMAIN,
            EntityType.CUSTOMER,
            EntityType.DEPARTMENT,
        ],
    )
    def test_new_source_types(self, source_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SUBJECT_TO,
            source_type,
            EntityType.REGULATION,
        )
        assert valid, reason

    @pytest.mark.parametrize(
        "target_type",
        [
            EntityType.POLICY,
            EntityType.CONTROL,
        ],
    )
    def test_new_target_types(self, target_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SUBJECT_TO,
            EntityType.SYSTEM,
            target_type,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SUBJECT_TO,
            EntityType.SYSTEM,
            EntityType.REGULATION,
        )
        assert valid, reason


class TestWidenedManagedBy:
    """managed_by now accepts Integration, Data_Asset, Network, Data_Domain as sources."""

    @pytest.mark.parametrize(
        "source_type",
        [
            EntityType.INTEGRATION,
            EntityType.DATA_ASSET,
            EntityType.NETWORK,
            EntityType.DATA_DOMAIN,
        ],
    )
    def test_new_source_types(self, source_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.MANAGED_BY,
            source_type,
            EntityType.DEPARTMENT,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.MANAGED_BY,
            EntityType.SYSTEM,
            EntityType.PERSON,
        )
        assert valid, reason


class TestWidenedDependsOn:
    """depends_on now accepts Business_Capability, Integration, Role as sources
    and Integration, Business_Capability as targets."""

    @pytest.mark.parametrize(
        "source_type",
        [
            EntityType.BUSINESS_CAPABILITY,
            EntityType.INTEGRATION,
            EntityType.ROLE,
        ],
    )
    def test_new_source_types(self, source_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.DEPENDS_ON,
            source_type,
            EntityType.SYSTEM,
        )
        assert valid, reason

    @pytest.mark.parametrize(
        "target_type",
        [
            EntityType.INTEGRATION,
            EntityType.BUSINESS_CAPABILITY,
        ],
    )
    def test_new_target_types(self, target_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.DEPENDS_ON,
            EntityType.SYSTEM,
            target_type,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.DEPENDS_ON,
            EntityType.SYSTEM,
            EntityType.SYSTEM,
        )
        assert valid, reason


class TestWidenedServes:
    """serves now accepts Department, Organizational_Unit as sources."""

    @pytest.mark.parametrize(
        "source_type",
        [
            EntityType.DEPARTMENT,
            EntityType.ORGANIZATIONAL_UNIT,
        ],
    )
    def test_new_source_types(self, source_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SERVES,
            source_type,
            EntityType.CUSTOMER,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SERVES,
            EntityType.PRODUCT,
            EntityType.CUSTOMER,
        )
        assert valid, reason


class TestWidenedBuys:
    """buys now accepts Product_Portfolio as target."""

    def test_product_portfolio_target(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.BUYS,
            EntityType.CUSTOMER,
            EntityType.PRODUCT_PORTFOLIO,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.BUYS,
            EntityType.CUSTOMER,
            EntityType.PRODUCT,
        )
        assert valid, reason


class TestWidenedContains:
    """contains now accepts Market_Segment, Product_Portfolio as sources
    and Customer, Product as targets."""

    @pytest.mark.parametrize(
        "source_type",
        [
            EntityType.MARKET_SEGMENT,
            EntityType.PRODUCT_PORTFOLIO,
        ],
    )
    def test_new_source_types(self, source_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.CONTAINS,
            source_type,
            EntityType.PRODUCT,
        )
        assert valid, reason

    @pytest.mark.parametrize(
        "target_type",
        [
            EntityType.CUSTOMER,
            EntityType.PRODUCT,
        ],
    )
    def test_new_target_types(self, target_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.CONTAINS,
            EntityType.MARKET_SEGMENT,
            target_type,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.CONTAINS,
            EntityType.DATA_DOMAIN,
            EntityType.DATA_ASSET,
        )
        assert valid, reason


class TestWidenedSupports:
    """supports now accepts Department, Integration as sources
    and Product_Portfolio as target."""

    @pytest.mark.parametrize(
        "source_type",
        [
            EntityType.DEPARTMENT,
            EntityType.INTEGRATION,
        ],
    )
    def test_new_source_types(self, source_type: EntityType) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SUPPORTS,
            source_type,
            EntityType.PRODUCT,
        )
        assert valid, reason

    def test_product_portfolio_target(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SUPPORTS,
            EntityType.SYSTEM,
            EntityType.PRODUCT_PORTFOLIO,
        )
        assert valid, reason

    def test_original_types_preserved(self) -> None:
        valid, reason = validate_relationship(
            RelationshipType.SUPPORTS,
            EntityType.SYSTEM,
            EntityType.BUSINESS_CAPABILITY,
        )
        assert valid, reason


class TestSchemaCompleteness:
    """Every RelationshipType should have a schema entry."""

    def test_all_types_have_schema(self) -> None:
        missing = [rt.value for rt in RelationshipType if rt not in RELATIONSHIP_SCHEMA]
        assert not missing, f"Missing schema entries: {missing}"

    def test_schema_sets_are_nonempty(self) -> None:
        for rt, (sources, targets) in RELATIONSHIP_SCHEMA.items():
            assert sources, f"{rt.value}: empty source set"
            assert targets, f"{rt.value}: empty target set"
