"""
Tests for core CheeseBrain functionality.
"""

import json
import tempfile
from pathlib import Path
from uuid import UUID

import pytest

from cheese_brain import CheeseBrain, Entity, EntityCategory


@pytest.fixture
def brain():
    """Create a temporary CheeseBrain instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        brain = CheeseBrain(str(db_path))
        yield brain
        brain.close()


def test_init_schema(brain):
    """Test schema initialization."""
    # Check that tables exist
    tables = brain.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    
    assert "entities" in table_names
    assert "audit_log" in table_names
    assert "metadata" in table_names


def test_add_entity(brain):
    """Test adding an entity."""
    entity = Entity(
        category=EntityCategory.PROJECT,
        title="Test Project",
        data={"url": "https://example.com", "status": "active"},
        tags=["test", "project"],
    )
    
    entity_id = brain.add_entity(entity)
    
    assert isinstance(entity_id, UUID)
    
    # Verify it was added
    retrieved = brain.get_by_id(entity_id)
    assert retrieved is not None
    assert retrieved.title == "Test Project"
    assert retrieved.category == EntityCategory.PROJECT
    assert "test" in retrieved.tags


def test_get_by_id(brain):
    """Test retrieving entity by ID."""
    entity = Entity(
        category=EntityCategory.TOOL,
        title="Test Tool",
        data={"install": "pip install test"},
        tags=["cli"],
    )
    
    entity_id = brain.add_entity(entity)
    retrieved = brain.get_by_id(entity_id)
    
    assert retrieved is not None
    assert retrieved.id == entity_id
    assert retrieved.title == "Test Tool"


def test_get_nonexistent(brain):
    """Test retrieving nonexistent entity."""
    fake_id = UUID("00000000-0000-0000-0000-000000000000")
    result = brain.get_by_id(fake_id)
    assert result is None


def test_search_keyword(brain):
    """Test keyword search."""
    # Add some entities
    brain.add_entity(Entity(
        category=EntityCategory.PROJECT,
        title="Email Gateway",
        data={"desc": "Processes email messages"},
        tags=["email"],
    ))
    brain.add_entity(Entity(
        category=EntityCategory.API,
        title="Gmail API",
        data={"endpoint": "gmail.googleapis.com"},
        tags=["google", "email"],
    ))
    brain.add_entity(Entity(
        category=EntityCategory.TOOL,
        title="curl",
        data={"purpose": "HTTP client"},
        tags=["http"],
    ))
    
    # Search for "email"
    results = brain.search("email")
    assert len(results) == 2
    
    # Search for "gmail"
    results = brain.search("gmail")
    assert len(results) == 1
    assert results[0].title == "Gmail API"


def test_search_with_category_filter(brain):
    """Test search with category filter."""
    brain.add_entity(Entity(
        category=EntityCategory.PROJECT,
        title="Project Alpha",
        tags=["alpha"],
    ))
    brain.add_entity(Entity(
        category=EntityCategory.TOOL,
        title="Tool Alpha",
        tags=["alpha"],
    ))
    
    results = brain.search("alpha", category="project")
    assert len(results) == 1
    assert results[0].category == EntityCategory.PROJECT


def test_search_with_tags(brain):
    """Test search with tag filter."""
    brain.add_entity(Entity(
        category=EntityCategory.PROJECT,
        title="Secure Project",
        tags=["security", "webapp"],
    ))
    brain.add_entity(Entity(
        category=EntityCategory.PROJECT,
        title="Another Project",
        tags=["webapp"],
    ))
    
    # Must have ALL tags
    results = brain.search("project", tags=["security", "webapp"])
    assert len(results) == 1
    assert results[0].title == "Secure Project"


def test_list_entities(brain):
    """Test listing entities."""
    brain.add_entity(Entity(category=EntityCategory.PROJECT, title="P1"))
    brain.add_entity(Entity(category=EntityCategory.TOOL, title="T1"))
    brain.add_entity(Entity(category=EntityCategory.TOOL, title="T2"))
    
    # List all
    results = brain.list_entities()
    assert len(results) == 3
    
    # List by category
    tools = brain.list_entities(category="tool")
    assert len(tools) == 2


def test_update_entity(brain):
    """Test updating an entity."""
    entity = Entity(
        category=EntityCategory.PROJECT,
        title="Old Title",
        data={"status": "draft"},
        tags=["old"],
    )
    
    entity_id = brain.add_entity(entity)
    
    # Update title
    updated = brain.update(entity_id, title="New Title")
    assert updated.title == "New Title"
    
    # Update data
    updated = brain.update(entity_id, data={"status": "published"})
    assert updated.data["status"] == "published"
    
    # Add tags
    updated = brain.update(entity_id, tags=["old", "new"])
    assert "new" in updated.tags


def test_delete_entity(brain):
    """Test soft delete."""
    entity = Entity(category=EntityCategory.PROJECT, title="To Delete")
    entity_id = brain.add_entity(entity)
    
    # Delete
    brain.delete(entity_id)
    
    # Should not be found in normal query
    assert brain.get_by_id(entity_id) is None
    
    # Should be found when including deleted
    deleted = brain.list_entities(include_deleted=True)
    assert len(deleted) == 1
    assert deleted[0].deleted_at is not None


def test_restore_entity(brain):
    """Test restoring a deleted entity."""
    entity = Entity(category=EntityCategory.PROJECT, title="To Restore")
    entity_id = brain.add_entity(entity)
    
    # Delete then restore
    brain.delete(entity_id)
    restored = brain.restore(entity_id)
    
    assert restored.deleted_at is None
    assert brain.get_by_id(entity_id) is not None


def test_export_import(brain):
    """Test JSON export and import."""
    # Add entities
    brain.add_entity(Entity(
        category=EntityCategory.PROJECT,
        title="Project 1",
        tags=["test"],
    ))
    brain.add_entity(Entity(
        category=EntityCategory.TOOL,
        title="Tool 1",
        tags=["test"],
    ))
    
    # Export
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        export_path = f.name
    
    count = brain.export_json(export_path)
    assert count == 2
    
    # Verify export file
    with open(export_path) as f:
        data = json.load(f)
    assert len(data) == 2
    
    # Import into new database
    with tempfile.TemporaryDirectory() as tmpdir:
        new_brain = CheeseBrain(str(Path(tmpdir) / "import.duckdb"))
        imported = new_brain.import_json(export_path)
        assert imported == 2
        
        results = new_brain.list_entities()
        assert len(results) == 2
        new_brain.close()
    
    # Cleanup
    Path(export_path).unlink()


def test_get_stats(brain):
    """Test statistics."""
    brain.add_entity(Entity(category=EntityCategory.PROJECT, title="P1"))
    brain.add_entity(Entity(category=EntityCategory.TOOL, title="T1"))
    entity_id = brain.add_entity(Entity(category=EntityCategory.PROJECT, title="P2"))
    
    # Delete one
    brain.delete(entity_id)
    
    stats = brain.get_stats()
    assert stats["total_entities"] == 2
    assert stats["deleted_entities"] == 1
    assert stats["by_category"]["project"] == 1
    assert stats["by_category"]["tool"] == 1
    assert stats["db_size_bytes"] > 0


def test_update_entity_with_relationships(brain):
    """Test updating an entity that has relationships (DuckDB foreign key workaround)."""
    from cheese_brain.models import RelationshipType
    
    # Create two entities
    tool_id = brain.add_entity(Entity(
        category=EntityCategory.TOOL,
        title="Python",
        data={"version": "3.11"},
        tags=["language"]
    ))
    
    project_id = brain.add_entity(Entity(
        category=EntityCategory.PROJECT,
        title="My Project",
        data={"status": "active"},
        tags=["dev"]
    ))
    
    # Create relationship
    rel_id = brain.add_relationship(
        from_id=project_id,
        to_id=tool_id,
        relationship_type=RelationshipType.USES
    )
    
    # Update the project entity (this should work despite the relationship)
    updated = brain.update(
        project_id,
        data={"status": "shipped", "version": "1.0"},
        tags=["dev", "shipped"]
    )
    
    # Verify update worked
    assert updated.data["status"] == "shipped"
    assert updated.data["version"] == "1.0"
    assert "shipped" in updated.tags
    
    # Verify relationship still exists
    relationships = brain.get_relationships(project_id)
    assert len(relationships) == 1
    rel, related_entity = relationships[0]
    assert related_entity.title == "Python"
    assert rel.relationship_type == RelationshipType.USES
