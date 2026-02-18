"""Tests for Phase 2 Sprint 3 (Advanced Queries) and Sprint 5 (Auto-Capture)."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cheese_brain import CheeseBrain, Entity, EntityCategory
from cheese_brain.auto_capture import EntityExtractor, scan_file


@pytest.fixture
def brain():
    """Create a temporary CheeseBrain instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        brain = CheeseBrain(str(db_path))
        yield brain
        brain.close()


def test_advanced_query_tag_modes_and_json_filter(brain):
    # Arrange
    brain.add_entity(
        Entity(
            category=EntityCategory.PROJECT,
            title="Project Alpha",
            data={"status": "active", "version": "1.0"},
            tags=["shipped", "security"],
        )
    )
    brain.add_entity(
        Entity(
            category=EntityCategory.PROJECT,
            title="Project Beta",
            data={"status": "active", "version": "2.0"},
            tags=["shipped"],
        )
    )
    brain.add_entity(
        Entity(
            category=EntityCategory.PROJECT,
            title="Project Gamma",
            data={"status": "draft"},
            tags=["security"],
        )
    )

    # Act: tags_mode=all should require BOTH tags
    results_all = brain.advanced_query(
        category="project",
        tags=["shipped", "security"],
        tags_mode="all",
        json_filter={"status": "active"},
        sort_by="title",
        sort_order="asc",
        limit=50,
    )

    # Assert
    assert [r.title for r in results_all] == ["Project Alpha"]

    # Act: tags_mode=any should accept either tag
    results_any = brain.advanced_query(
        category="project",
        tags=["security"],
        tags_mode="any",
        json_filter={"status": "active"},
        sort_by="title",
        sort_order="asc",
        limit=50,
    )

    # Assert: only Alpha is active+security
    assert [r.title for r in results_any] == ["Project Alpha"]

    # Act: version filter should isolate Beta
    results_version = brain.advanced_query(
        category="project",
        tags=["shipped"],
        tags_mode="any",
        json_filter={"status": "active", "version": "2.0"},
        sort_by="title",
        sort_order="asc",
    )

    assert [r.title for r in results_version] == ["Project Beta"]


def test_advanced_query_date_range(brain):
    # Arrange: create entities, then update their created_at for deterministic date filtering
    id_old = brain.add_entity(Entity(category=EntityCategory.TOOL, title="Old Tool"))
    id_new = brain.add_entity(Entity(category=EntityCategory.TOOL, title="New Tool"))

    old_dt = datetime(2026, 1, 1)
    new_dt = datetime(2026, 2, 1)

    brain.conn.execute("UPDATE entities SET created_at = ? WHERE id = ?", [old_dt, str(id_old)])
    brain.conn.execute("UPDATE entities SET created_at = ? WHERE id = ?", [new_dt, str(id_new)])

    # Act
    results = brain.advanced_query(
        category="tool",
        since=datetime(2026, 1, 15),
        until=datetime(2026, 2, 15),
        sort_by="created_at",
        sort_order="asc",
    )

    # Assert
    assert [r.title for r in results] == ["New Tool"]


def test_auto_capture_extractor_explicit_and_generic():
    text = """# Daily Note

## 🧀 Cheese Digest
- **Tool:** pytest - Python testing framework
- **Workflow:** Daily Backup - Nightly backups

Other:
- tool: mypy (python,typing) - Static type checker
"""

    extractor = EntityExtractor()
    entities = extractor.extract_from_text(text, confidence_threshold=0.7)

    titles = sorted([e["title"] for e in entities])
    assert "pytest" in titles
    assert "Daily Backup" in titles
    assert "mypy" in titles


def test_scan_file_deduplicates(tmp_path: Path):
    md = tmp_path / "note.md"
    md.write_text(
        """## 🧀 Cheese Digest\n- **Tool:** pytest - Python testing framework\n\n**Tool:** pytest - Duplicate mention\n""",
        encoding="utf-8",
    )

    results = scan_file(str(md), confidence_threshold=0.7)
    assert results["total"] == 1
    assert results["entities"][0]["title"] == "pytest"
