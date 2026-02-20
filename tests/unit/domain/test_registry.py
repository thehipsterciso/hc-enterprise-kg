"""Tests for EntityRegistry."""

from domain.base import EntityType
from domain.entities.person import Person
from domain.registry import EntityRegistry


class TestEntityRegistry:
    def test_auto_discover(self):
        EntityRegistry.auto_discover()
        assert EntityRegistry.is_registered(EntityType.PERSON)
        assert EntityRegistry.is_registered(EntityType.SYSTEM)
        assert len(EntityRegistry.all_types()) == 30  # 12 original + 18 stubs

    def test_get_registered_type(self):
        EntityRegistry.auto_discover()
        cls = EntityRegistry.get(EntityType.PERSON)
        assert cls is Person

    def test_get_unregistered_raises(self):
        EntityRegistry.clear()
        try:
            EntityRegistry.get(EntityType.PERSON)
            raise AssertionError("Should have raised KeyError")
        except KeyError:
            pass
        # Re-register for other tests
        EntityRegistry.auto_discover()
