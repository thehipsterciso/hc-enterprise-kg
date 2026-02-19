"""Shared pytest fixtures for the enterprise knowledge graph tests."""

from __future__ import annotations

import pytest

from domain.base import BaseRelationship, RelationshipType
from domain.entities.department import Department
from domain.entities.person import Person
from domain.entities.system import System
from domain.registry import EntityRegistry
from engine.factory import GraphEngineFactory
from engine.networkx_engine import NetworkXGraphEngine
from graph.knowledge_graph import KnowledgeGraph


@pytest.fixture(autouse=True)
def _auto_discover() -> None:
    """Auto-discover entity types and engine backends before each test."""
    EntityRegistry.auto_discover()
    GraphEngineFactory.auto_discover()


@pytest.fixture
def engine() -> NetworkXGraphEngine:
    """Create a fresh NetworkX engine."""
    return NetworkXGraphEngine()


@pytest.fixture
def kg() -> KnowledgeGraph:
    """Create a fresh KnowledgeGraph."""
    return KnowledgeGraph(backend="networkx", track_events=True)


@pytest.fixture
def sample_person() -> Person:
    """Create a sample Person entity."""
    return Person(
        id="person-1",
        first_name="Alice",
        last_name="Smith",
        name="Alice Smith",
        email="alice.smith@acme.com",
        title="Software Engineer",
        employee_id="EMP-001",
        is_active=True,
    )


@pytest.fixture
def sample_department() -> Department:
    """Create a sample Department entity."""
    return Department(
        id="dept-1",
        name="Engineering",
        description="Engineering department",
        code="ENG",
        headcount=50,
    )


@pytest.fixture
def sample_system() -> System:
    """Create a sample System entity."""
    return System(
        id="sys-1",
        name="Web Application",
        system_type="application",
        hostname="webapp-001",
        ip_address="10.0.1.100",
        os="Linux",
        criticality="high",
        is_internet_facing=True,
    )


@pytest.fixture
def sample_relationship() -> BaseRelationship:
    """Create a sample relationship."""
    return BaseRelationship(
        id="rel-1",
        relationship_type=RelationshipType.WORKS_IN,
        source_id="person-1",
        target_id="dept-1",
    )


@pytest.fixture
def populated_kg(
    kg: KnowledgeGraph,
    sample_person: Person,
    sample_department: Department,
    sample_system: System,
) -> KnowledgeGraph:
    """Create a KG with sample entities and relationships."""
    kg.add_entity(sample_person)
    kg.add_entity(sample_department)
    kg.add_entity(sample_system)

    kg.add_relationship(
        BaseRelationship(
            relationship_type=RelationshipType.WORKS_IN,
            source_id=sample_person.id,
            target_id=sample_department.id,
        )
    )
    kg.add_relationship(
        BaseRelationship(
            relationship_type=RelationshipType.RESPONSIBLE_FOR,
            source_id=sample_department.id,
            target_id=sample_system.id,
        )
    )

    return kg
