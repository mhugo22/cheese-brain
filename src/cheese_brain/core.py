"""
Core CheeseBrain class - main interface to the knowledge base.
"""

import duckdb
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from cheese_brain.models import Entity, EntityCategory


class CheeseBrain:
    """Main interface to Cheese Brain knowledge base."""

    def __init__(self, db_path: str = "~/.cheese-brain/cheese-brain.duckdb"):
        """Initialize connection to DuckDB database.
        
        Args:
            db_path: Path to database file (default: ~/.cheese-brain/cheese-brain.duckdb)
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables if they don't exist. Idempotent."""
        # Check if schema exists
        tables = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        if "metadata" not in table_names:
            # First-time setup
            self._create_schema()
        else:
            # Check schema version for migrations
            version = self.conn.execute(
                "SELECT json_extract_string(value, '$.version') FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
            if version and version[0] != "1.0.0":
                # Future: handle migrations
                pass

    def _create_schema(self) -> None:
        """Create initial schema (v1.0.0)."""
        # Sequence for audit log
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS audit_seq START 1")

        # Main entities table
        self.conn.execute("""
            CREATE TABLE entities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                category VARCHAR NOT NULL CHECK (category IN (
                    'project', 'email', 'api', 'tool', 'decision',
                    'code_snippet', 'contact', 'bookmark', 'config_location',
                    'failed_experiment', 'problem', 'learning_note',
                    'workflow', 'troubleshooting', 'infrastructure',
                    'meeting_note', 'idea', 'habit', 'dependency',
                    'environment_config', 'vendor_license', 'metric'
                )),
                title VARCHAR(500) NOT NULL,
                data JSON NOT NULL,
                tags VARCHAR[] DEFAULT [],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
        """)

        # Indexes
        self.conn.execute("CREATE INDEX idx_category ON entities(category)")
        self.conn.execute("CREATE INDEX idx_created ON entities(created_at DESC)")
        self.conn.execute("CREATE INDEX idx_title_lower ON entities(LOWER(title))")

        # FTS extension
        try:
            self.conn.execute("INSTALL fts")
            self.conn.execute("LOAD fts")
            self.conn.execute("PRAGMA create_fts_index('entities', 'id', 'title', 'category')")
        except Exception:
            # FTS optional - continue without it
            pass

        # Audit log (no foreign key constraint - keep logs even if entity deleted)
        self.conn.execute("""
            CREATE TABLE audit_log (
                id BIGINT PRIMARY KEY DEFAULT nextval('audit_seq'),
                entity_id UUID NOT NULL,
                action VARCHAR(20) NOT NULL,
                old_data JSON,
                new_data JSON NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("CREATE INDEX idx_audit_entity ON audit_log(entity_id)")
        self.conn.execute("CREATE INDEX idx_audit_timestamp ON audit_log(changed_at DESC)")

        # Metadata table
        self.conn.execute("""
            CREATE TABLE metadata (
                key VARCHAR PRIMARY KEY,
                value JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initial metadata
        self.conn.execute("""
            INSERT INTO metadata (key, value) VALUES
                ('schema_version', '{"version": "1.0.0", "created_at": "2026-02-17T00:00:00Z"}'),
                ('entity_count', '{"count": 0}')
        """)

    def add_entity(self, entity: Entity) -> UUID:
        """Add a new entity to the knowledge base.
        
        Args:
            entity: Entity object to add
            
        Returns:
            UUID of the created entity
        """
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # Insert entity (let DuckDB handle timestamps)
            self.conn.execute(
                """
                INSERT INTO entities (id, category, title, data, tags)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    str(entity.id),
                    entity.category.value,
                    entity.title,
                    json.dumps(entity.data),
                    entity.tags,
                ],
            )

            # Log to audit
            self.conn.execute(
                """
                INSERT INTO audit_log (entity_id, action, new_data)
                VALUES (?, 'create', ?)
                """,
                [str(entity.id), json.dumps(entity.model_dump(), default=str)],
            )

            self.conn.execute("COMMIT")
            return entity.id
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def get_by_id(self, entity_id: UUID) -> Optional[Entity]:
        """Fetch an entity by ID.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Entity object or None if not found
        """
        result = self.conn.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NULL",
            [str(entity_id)],
        ).fetchone()

        if not result:
            return None

        return self._row_to_entity(result)

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[Entity]:
        """Search entities with multi-keyword matching.
        
        Args:
            query: Search query (space-separated keywords)
            category: Optional category filter
            tags: Optional list of tags (entity must have ALL tags)
            since: Optional date filter (entities created after this date)
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        # Tokenize query
        keywords = query.lower().split()

        # Build WHERE clauses
        where_clauses = ["deleted_at IS NULL"]
        params = []

        # Multi-keyword search across title, data, and tags
        for keyword in keywords:
            where_clauses.append(
                "(LOWER(title) LIKE ? OR CAST(data AS VARCHAR) ILIKE ? OR list_has_any(tags, [?]))"
            )
            params.extend([f"%{keyword}%", f"%{keyword}%", keyword])

        # Category filter
        if category:
            where_clauses.append("category = ?")
            params.append(category)

        # Tag filters (must have ALL tags)
        if tags:
            for tag in tags:
                where_clauses.append("list_contains(tags, ?)")
                params.append(tag)

        # Date filter
        if since:
            where_clauses.append("created_at >= ?")
            params.append(since)

        # Build final query
        sql = f"""
            SELECT * FROM entities
            WHERE {' AND '.join(where_clauses)}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(limit)

        results = self.conn.execute(sql, params).fetchall()
        return [self._row_to_entity(row) for row in results]

    def list_entities(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> list[Entity]:
        """List entities with optional filters.
        
        Args:
            category: Optional category filter
            limit: Maximum number of results
            include_deleted: Include soft-deleted entities
            
        Returns:
            List of entities
        """
        where_clauses = []
        params = []

        if not include_deleted:
            where_clauses.append("deleted_at IS NULL")

        if category:
            where_clauses.append("category = ?")
            params.append(category)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        sql = f"""
            SELECT * FROM entities
            {where_sql}
            ORDER BY updated_at DESC
            LIMIT ?
        """
        params.append(limit)

        results = self.conn.execute(sql, params).fetchall()
        return [self._row_to_entity(row) for row in results]

    def update(self, entity_id: UUID, **kwargs) -> Entity:
        """Update an entity's fields.
        
        Args:
            entity_id: UUID of entity to update
            **kwargs: Fields to update (title, data, tags)
            
        Returns:
            Updated Entity object
        """
        # Fetch current entity
        current = self.get_by_id(entity_id)
        if not current:
            raise ValueError(f"Entity {entity_id} not found")

        # Build UPDATE statement
        set_clauses = ["updated_at = CURRENT_TIMESTAMP"]
        params = []

        if "title" in kwargs:
            set_clauses.append("title = ?")
            params.append(kwargs["title"])

        if "data" in kwargs:
            set_clauses.append("data = ?")
            params.append(json.dumps(kwargs["data"]))

        if "tags" in kwargs:
            set_clauses.append("tags = ?")
            params.append(kwargs["tags"])

        params.append(str(entity_id))

        self.conn.execute("BEGIN TRANSACTION")
        try:
            # Update entity
            self.conn.execute(
                f"UPDATE entities SET {', '.join(set_clauses)} WHERE id = ?",
                params,
            )

            # Fetch updated entity
            updated = self.get_by_id(entity_id)

            # Log to audit
            self.conn.execute(
                """
                INSERT INTO audit_log (entity_id, action, old_data, new_data)
                VALUES (?, 'update', ?, ?)
                """,
                [
                    str(entity_id),
                    json.dumps(current.model_dump(), default=str),
                    json.dumps(updated.model_dump(), default=str),
                ],
            )

            self.conn.execute("COMMIT")
            return updated
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def delete(self, entity_id: UUID) -> None:
        """Soft delete an entity (set deleted_at timestamp).
        
        Args:
            entity_id: UUID of entity to delete
        """
        entity = self.get_by_id(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        self.conn.execute("BEGIN TRANSACTION")
        try:
            self.conn.execute(
                "UPDATE entities SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                [str(entity_id)],
            )

            self.conn.execute(
                """
                INSERT INTO audit_log (entity_id, action, new_data)
                VALUES (?, 'delete', ?)
                """,
                [str(entity_id), json.dumps({"deleted_at": datetime.now(timezone.utc).isoformat()})],
            )

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def restore(self, entity_id: UUID) -> Entity:
        """Restore a soft-deleted entity.
        
        Args:
            entity_id: UUID of entity to restore
            
        Returns:
            Restored Entity object
        """
        # Check if entity exists and is deleted
        result = self.conn.execute(
            "SELECT * FROM entities WHERE id = ? AND deleted_at IS NOT NULL",
            [str(entity_id)],
        ).fetchone()

        if not result:
            raise ValueError(f"Entity {entity_id} not found or not deleted")

        self.conn.execute("BEGIN TRANSACTION")
        try:
            self.conn.execute(
                "UPDATE entities SET deleted_at = NULL WHERE id = ?",
                [str(entity_id)],
            )

            self.conn.execute(
                """
                INSERT INTO audit_log (entity_id, action, new_data)
                VALUES (?, 'restore', ?)
                """,
                [str(entity_id), json.dumps({"restored": True})],
            )

            self.conn.execute("COMMIT")
            return self.get_by_id(entity_id)
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def export_json(self, output_path: str) -> int:
        """Export all non-deleted entities to JSON.
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            Number of entities exported
        """
        entities = self.list_entities(limit=999999, include_deleted=False)
        output = [e.model_dump() for e in entities]

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2, default=str)

        return len(output)

    def import_json(self, input_path: str, merge: bool = False) -> int:
        """Import entities from JSON backup.
        
        Args:
            input_path: Path to JSON file
            merge: If True, update existing entities; if False, error on duplicates
            
        Returns:
            Number of entities imported
        """
        with open(input_path, "r") as f:
            data = json.load(f)

        count = 0
        for item in data:
            entity = Entity(**item)
            
            if merge:
                # Check if exists
                existing = self.get_by_id(entity.id)
                if existing:
                    # Update
                    self.update(
                        entity.id,
                        title=entity.title,
                        data=entity.data,
                        tags=entity.tags,
                    )
                else:
                    # Insert
                    self.add_entity(entity)
                count += 1
            else:
                # Insert (will error if duplicate)
                self.add_entity(entity)
                count += 1

        return count

    def export_parquet(self, output_path: str) -> int:
        """Export all non-deleted entities to Parquet format.
        
        Parquet provides ~9x compression vs JSON while maintaining full fidelity.
        
        Args:
            output_path: Path to output Parquet file
            
        Returns:
            Number of entities exported
        """
        # Export to temporary table, then to Parquet
        self.conn.execute("""
            COPY (
                SELECT 
                    id::VARCHAR as id,
                    category,
                    title,
                    data,
                    tags,
                    created_at,
                    updated_at,
                    deleted_at
                FROM entities
                WHERE deleted_at IS NULL
            ) TO ? (FORMAT PARQUET)
        """, [output_path])

        # Count entities exported
        count = self.conn.execute(
            "SELECT COUNT(*) FROM entities WHERE deleted_at IS NULL"
        ).fetchone()[0]

        return count

    def import_parquet(self, input_path: str, merge: bool = False) -> int:
        """Import entities from Parquet backup.
        
        Args:
            input_path: Path to Parquet file
            merge: If True, update existing entities; if False, error on duplicates
            
        Returns:
            Number of entities imported
        """
        # Load from Parquet into temporary table
        temp_table = "temp_import"
        self.conn.execute(f"DROP TABLE IF EXISTS {temp_table}")
        self.conn.execute(f"""
            CREATE TABLE {temp_table} AS 
            SELECT * FROM read_parquet(?)
        """, [input_path])

        # Get data and convert to entities
        rows = self.conn.execute(f"SELECT * FROM {temp_table}").fetchall()
        
        count = 0
        for row in rows:
            entity = Entity(
                id=UUID(row[0]),
                category=EntityCategory(row[1]),
                title=row[2],
                data=row[3] if isinstance(row[3], dict) else json.loads(row[3]),
                tags=row[4] if row[4] else [],
                created_at=row[5],
                updated_at=row[6],
                deleted_at=row[7],
            )
            
            if merge:
                # Check if exists
                existing = self.get_by_id(entity.id)
                if existing:
                    # Update
                    self.update(
                        entity.id,
                        title=entity.title,
                        data=entity.data,
                        tags=entity.tags,
                    )
                else:
                    # Insert
                    self.add_entity(entity)
                count += 1
            else:
                # Insert (will error if duplicate)
                self.add_entity(entity)
                count += 1

        # Cleanup
        self.conn.execute(f"DROP TABLE {temp_table}")
        return count

    def get_stats(self) -> dict:
        """Get database statistics.
        
        Returns:
            Dictionary with stats (entity count, categories, disk size)
        """
        total = self.conn.execute("SELECT COUNT(*) FROM entities WHERE deleted_at IS NULL").fetchone()[0]
        deleted = self.conn.execute("SELECT COUNT(*) FROM entities WHERE deleted_at IS NOT NULL").fetchone()[0]
        
        by_category = self.conn.execute("""
            SELECT category, COUNT(*) as cnt
            FROM entities
            WHERE deleted_at IS NULL
            GROUP BY category
            ORDER BY cnt DESC
        """).fetchall()

        db_size = self.db_path.stat().st_size

        return {
            "total_entities": total,
            "deleted_entities": deleted,
            "by_category": {cat: cnt for cat, cnt in by_category},
            "db_size_bytes": db_size,
            "db_size_mb": round(db_size / 1024 / 1024, 2),
        }

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    def _row_to_entity(self, row) -> Entity:
        """Convert a database row to an Entity object."""
        # DuckDB returns UUID objects directly, not strings
        entity_id = row[0] if isinstance(row[0], UUID) else UUID(row[0])
        
        return Entity(
            id=entity_id,
            category=EntityCategory(row[1]),
            title=row[2],
            data=json.loads(row[3]) if isinstance(row[3], str) else row[3],
            tags=row[4] if row[4] else [],
            created_at=row[5],
            updated_at=row[6],
            deleted_at=row[7],
        )
