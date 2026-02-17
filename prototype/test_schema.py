#!/usr/bin/env python3
"""
Cheese Brain - DuckDB Schema Prototype
Tests what actually works vs. what we assumed from PostgreSQL.
"""

import duckdb
import json
import time
import os

DB_PATH = "/tmp/cheese-brain-prototype.duckdb"

# Clean start
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = duckdb.connect(DB_PATH)

print("=" * 60)
print(f"DuckDB Version: {duckdb.__version__}")
print("=" * 60)

# ============================================================
# TEST 1: Basic table creation
# ============================================================
print("\n--- TEST 1: Basic table creation ---")
try:
    conn.execute("""
        CREATE TABLE entities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category VARCHAR NOT NULL,
            title VARCHAR(500) NOT NULL,
            data JSON NOT NULL,
            tags VARCHAR[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP
        )
    """)
    print("✅ Basic table creation works")
except Exception as e:
    print(f"❌ Basic table creation failed: {e}")

# ============================================================
# TEST 2: CHECK constraint on category
# ============================================================
print("\n--- TEST 2: CHECK constraint ---")
try:
    conn.execute("DROP TABLE IF EXISTS entities")
    conn.execute("""
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
    print("✅ CHECK constraint works")
except Exception as e:
    print(f"❌ CHECK constraint failed: {e}")

# ============================================================
# TEST 3: Index types
# ============================================================
print("\n--- TEST 3: Index types ---")

# Simple B-tree index
try:
    conn.execute("CREATE INDEX idx_category ON entities(category)")
    print("✅ B-tree index on category works")
except Exception as e:
    print(f"❌ B-tree index on category failed: {e}")

# Index with expression
try:
    conn.execute("CREATE INDEX idx_title_lower ON entities(LOWER(title))")
    print("✅ Expression index on LOWER(title) works")
except Exception as e:
    print(f"❌ Expression index failed: {e}")

# Partial index (WHERE clause)
try:
    conn.execute("CREATE INDEX idx_category_active ON entities(category) WHERE deleted_at IS NULL")
    print("✅ Partial index (WHERE deleted_at IS NULL) works")
except Exception as e:
    print(f"❌ Partial index failed: {e}")

# Index on timestamp
try:
    conn.execute("CREATE INDEX idx_created ON entities(created_at DESC)")
    print("✅ Descending index on timestamp works")
except Exception as e:
    print(f"❌ Timestamp index failed: {e}")

# GIN index on array (PostgreSQL syntax)
try:
    conn.execute("CREATE INDEX idx_tags_gin ON entities USING GIN(tags)")
    print("✅ GIN index on tags works")
except Exception as e:
    print(f"❌ GIN index on tags failed: {e}")
    # Try regular index on array
    try:
        conn.execute("CREATE INDEX idx_tags ON entities(tags)")
        print("  ✅ Regular index on tags works instead")
    except Exception as e2:
        print(f"  ❌ Regular index on tags also failed: {e2}")

# ============================================================
# TEST 4: Insert entities
# ============================================================
print("\n--- TEST 4: Insert entities ---")
try:
    conn.execute("""
        INSERT INTO entities (category, title, data, tags) VALUES 
        ('project', 'SketchySkills', '{"url": "https://sketchyskills.vercel.app", "status": "shipped"}', ['security', 'webapp']),
        ('email', 'Gabby Email', '{"address": "gabby@example.com", "purpose": "personal"}', ['email', 'personal']),
        ('tool', 'DuckDB', '{"install": "pip install duckdb", "version": "1.4.4"}', ['database', 'analytics']),
        ('decision', 'Why DuckDB over SQLite', '{"reason": "faster analytics", "alternatives": ["SQLite", "TinyDB"]}', ['architecture', 'database']),
        ('contact', 'John Doe', '{"context": "met at conference", "expertise": ["python", "data"]}', ['conference', 'python'])
    """)
    count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    print(f"✅ Inserted 5 entities, count: {count}")
except Exception as e:
    print(f"❌ Insert failed: {e}")

# ============================================================
# TEST 5: Array operations
# ============================================================
print("\n--- TEST 5: Array operations ---")

# PostgreSQL @> (array contains)
try:
    result = conn.execute("SELECT title FROM entities WHERE tags @> ['security']").fetchall()
    print(f"✅ @> (array contains) works: {result}")
except Exception as e:
    print(f"❌ @> operator failed: {e}")

# list_contains
try:
    result = conn.execute("SELECT title FROM entities WHERE list_contains(tags, 'security')").fetchall()
    print(f"✅ list_contains() works: {result}")
except Exception as e:
    print(f"❌ list_contains() failed: {e}")

# list_has_any (overlap)
try:
    result = conn.execute("SELECT title FROM entities WHERE list_has_any(tags, ['security', 'python'])").fetchall()
    print(f"✅ list_has_any() works: {result}")
except Exception as e:
    print(f"❌ list_has_any() failed: {e}")

# PostgreSQL && (array overlap)
try:
    result = conn.execute("SELECT title FROM entities WHERE tags && ['security', 'python']").fetchall()
    print(f"✅ && (array overlap) works: {result}")
except Exception as e:
    print(f"❌ && operator failed: {e}")

# array_contains (alternative)
try:
    result = conn.execute("SELECT title FROM entities WHERE array_contains(tags, 'security')").fetchall()
    print(f"✅ array_contains() works: {result}")
except Exception as e:
    print(f"❌ array_contains() failed: {e}")

# Multiple tag check using list_contains with AND
try:
    result = conn.execute("""
        SELECT title FROM entities 
        WHERE list_contains(tags, 'security') AND list_contains(tags, 'webapp')
    """).fetchall()
    print(f"✅ Multiple list_contains() AND works: {result}")
except Exception as e:
    print(f"❌ Multiple list_contains() failed: {e}")

# unnest for tag analysis
try:
    result = conn.execute("""
        SELECT unnest(tags) as tag, COUNT(*) as cnt
        FROM entities
        GROUP BY tag
        ORDER BY cnt DESC
    """).fetchall()
    print(f"✅ unnest() for tag analysis works: {result}")
except Exception as e:
    print(f"❌ unnest() failed: {e}")

# ============================================================
# TEST 6: JSON operations
# ============================================================
print("\n--- TEST 6: JSON operations ---")

# json_extract_string (->>) equivalent
try:
    result = conn.execute("SELECT title, data->>'url' as url FROM entities WHERE category = 'project'").fetchall()
    print(f"✅ ->> (json extract string) works: {result}")
except Exception as e:
    print(f"❌ ->> failed: {e}")
    try:
        result = conn.execute("SELECT title, json_extract_string(data, '$.url') as url FROM entities WHERE category = 'project'").fetchall()
        print(f"  ✅ json_extract_string() works: {result}")
    except Exception as e2:
        print(f"  ❌ json_extract_string() also failed: {e2}")

# json_extract with path
try:
    result = conn.execute("SELECT title, data->'$.status' as status FROM entities WHERE category = 'project'").fetchall()
    print(f"✅ -> with json path works: {result}")
except Exception as e:
    print(f"❌ -> json path failed: {e}")
    try:
        result = conn.execute("SELECT title, json_extract(data, '$.status') as status FROM entities WHERE category = 'project'").fetchall()
        print(f"  ✅ json_extract() works: {result}")
    except Exception as e2:
        print(f"  ❌ json_extract() also failed: {e2}")

# Filter on JSON field
try:
    result = conn.execute("""
        SELECT title FROM entities 
        WHERE json_extract_string(data, '$.status') = 'shipped'
    """).fetchall()
    print(f"✅ Filter on JSON field works: {result}")
except Exception as e:
    print(f"❌ Filter on JSON field failed: {e}")

# ============================================================
# TEST 7: Full-Text Search
# ============================================================
print("\n--- TEST 7: Full-Text Search ---")

# FTS index
try:
    conn.execute("INSTALL fts; LOAD fts;")
    print("✅ FTS extension installed/loaded")
except Exception as e:
    print(f"❌ FTS extension failed: {e}")

# Create FTS index using PRAGMA
try:
    conn.execute("""
        PRAGMA create_fts_index('entities', 'id', 'title', 'category')
    """)
    print("✅ FTS index created via PRAGMA")
except Exception as e:
    print(f"❌ FTS PRAGMA failed: {e}")

# FTS query
try:
    result = conn.execute("""
        SELECT title, fts_main_entities.match_bm25(id, 'security') as score
        FROM entities
        WHERE score IS NOT NULL
        ORDER BY score DESC
    """).fetchall()
    print(f"✅ FTS BM25 query works: {result}")
except Exception as e:
    print(f"❌ FTS query failed: {e}")
    # Try alternative FTS syntax
    try:
        result = conn.execute("""
            SELECT title, score
            FROM (
                SELECT *, fts_main_entities.match_bm25(id, 'sketchy') as score
                FROM entities
            ) sq
            WHERE score IS NOT NULL
        """).fetchall()
        print(f"  ✅ Alternative FTS query works: {result}")
    except Exception as e2:
        print(f"  ❌ Alternative FTS also failed: {e2}")

# ============================================================
# TEST 8: Audit log table
# ============================================================
print("\n--- TEST 8: Audit log table ---")

# BIGSERIAL test
try:
    conn.execute("""
        CREATE TABLE audit_log_v1 (
            id BIGSERIAL PRIMARY KEY,
            entity_id UUID,
            action VARCHAR(20) NOT NULL,
            old_data JSON,
            new_data JSON NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ BIGSERIAL works")
except Exception as e:
    print(f"❌ BIGSERIAL failed: {e}")

# Try INTEGER with GENERATED ALWAYS
try:
    conn.execute("""
        CREATE TABLE audit_log_v2 (
            id BIGINT PRIMARY KEY DEFAULT nextval('audit_seq'),
            entity_id UUID,
            action VARCHAR(20) NOT NULL,
            old_data JSON,
            new_data JSON NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ BIGINT with sequence works")
except Exception as e:
    print(f"❌ Sequence approach failed: {e}")

# Try CREATE SEQUENCE
try:
    conn.execute("CREATE SEQUENCE audit_seq START 1")
    conn.execute("""
        CREATE TABLE audit_log_v3 (
            id BIGINT PRIMARY KEY DEFAULT nextval('audit_seq'),
            entity_id UUID,
            action VARCHAR(20) NOT NULL,
            old_data JSON,
            new_data JSON NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO audit_log_v3 (entity_id, action, new_data) 
        VALUES (gen_random_uuid(), 'create', '{"test": true}')
    """)
    result = conn.execute("SELECT * FROM audit_log_v3").fetchall()
    print(f"✅ CREATE SEQUENCE + nextval works: {result}")
except Exception as e:
    print(f"❌ Sequence approach failed: {e}")

# ============================================================
# TEST 9: FOREIGN KEY
# ============================================================
print("\n--- TEST 9: Foreign keys ---")
try:
    conn.execute("""
        CREATE TABLE fk_test (
            id BIGINT,
            entity_id UUID REFERENCES entities(id),
            note VARCHAR
        )
    """)
    print("✅ Foreign key reference works")
except Exception as e:
    print(f"❌ Foreign key failed: {e}")

# ============================================================
# TEST 10: Keyword search patterns
# ============================================================
print("\n--- TEST 10: Keyword search patterns ---")

# LIKE with case insensitive
try:
    result = conn.execute("""
        SELECT title FROM entities 
        WHERE LOWER(title) LIKE '%sketchy%'
        AND deleted_at IS NULL
    """).fetchall()
    print(f"✅ Case-insensitive LIKE works: {result}")
except Exception as e:
    print(f"❌ LIKE search failed: {e}")

# ILIKE (case insensitive LIKE)
try:
    result = conn.execute("""
        SELECT title FROM entities 
        WHERE title ILIKE '%sketchy%'
        AND deleted_at IS NULL
    """).fetchall()
    print(f"✅ ILIKE works (simpler!): {result}")
except Exception as e:
    print(f"❌ ILIKE failed: {e}")

# Search across title AND JSON data
try:
    result = conn.execute("""
        SELECT title FROM entities 
        WHERE title ILIKE '%gabby%' 
           OR CAST(data AS VARCHAR) ILIKE '%gabby%'
    """).fetchall()
    print(f"✅ Search across title + JSON works: {result}")
except Exception as e:
    print(f"❌ Cross-field search failed: {e}")

# Multi-keyword search (split on spaces)
try:
    result = conn.execute("""
        SELECT title FROM entities 
        WHERE (title ILIKE '%email%' OR CAST(data AS VARCHAR) ILIKE '%email%')
          AND (title ILIKE '%gabby%' OR CAST(data AS VARCHAR) ILIKE '%gabby%')
          AND deleted_at IS NULL
    """).fetchall()
    print(f"✅ Multi-keyword AND search works: {result}")
except Exception as e:
    print(f"❌ Multi-keyword search failed: {e}")

# ============================================================
# TEST 11: Export/Import
# ============================================================
print("\n--- TEST 11: Export/Import ---")

# Export to JSON
try:
    conn.execute("COPY entities TO '/tmp/cheese-brain-export.json' (FORMAT JSON, ARRAY true)")
    print("✅ Export to JSON works")
    with open('/tmp/cheese-brain-export.json', 'r') as f:
        data = json.load(f)
        print(f"  Exported {len(data)} records")
except Exception as e:
    print(f"❌ JSON export failed: {e}")
    # Try alternative
    try:
        conn.execute("COPY (SELECT * FROM entities) TO '/tmp/cheese-brain-export.json'")
        print(f"  ✅ Alternative COPY works")
    except Exception as e2:
        print(f"  ❌ Alternative also failed: {e2}")

# Export to Parquet
try:
    conn.execute("COPY entities TO '/tmp/cheese-brain-export.parquet' (FORMAT PARQUET)")
    size = os.path.getsize('/tmp/cheese-brain-export.parquet')
    print(f"✅ Export to Parquet works ({size} bytes)")
except Exception as e:
    print(f"❌ Parquet export failed: {e}")

# Export to CSV
try:
    conn.execute("COPY entities TO '/tmp/cheese-brain-export.csv' (FORMAT CSV, HEADER)")
    print("✅ Export to CSV works")
except Exception as e:
    print(f"❌ CSV export failed: {e}")

# ============================================================
# TEST 12: Performance benchmark
# ============================================================
print("\n--- TEST 12: Performance benchmark ---")

# Bulk insert 1000 entities
start = time.time()
for i in range(1000):
    conn.execute(f"""
        INSERT INTO entities (category, title, data, tags) VALUES 
        ('tool', 'TestTool-{i}', '{{"index": {i}, "desc": "test entity number {i}"}}', ['test', 'benchmark', 'tool-{i % 10}'])
    """)
elapsed = time.time() - start
print(f"Insert 1000 entities: {elapsed:.3f}s ({1000/elapsed:.0f} ops/s)")

# Batch insert 1000 more
start = time.time()
values = []
for i in range(1000, 2000):
    values.append(f"('project', 'TestProject-{i}', '{{\"index\": {i}}}', ['batch', 'test'])")
conn.execute(f"INSERT INTO entities (category, title, data, tags) VALUES {','.join(values)}")
elapsed = time.time() - start
print(f"Batch insert 1000 entities: {elapsed:.3f}s ({1000/elapsed:.0f} ops/s)")

total = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
print(f"Total entities: {total}")

# Keyword search at scale
start = time.time()
for _ in range(100):
    conn.execute("SELECT * FROM entities WHERE title ILIKE '%TestTool-50%' AND deleted_at IS NULL").fetchall()
elapsed = time.time() - start
print(f"Keyword search (100 iterations, {total} entities): {elapsed*10:.2f}ms avg")

# Category filter at scale
start = time.time()
for _ in range(100):
    conn.execute("SELECT * FROM entities WHERE category = 'project' AND deleted_at IS NULL").fetchall()
elapsed = time.time() - start
print(f"Category filter (100 iterations): {elapsed*10:.2f}ms avg")

# Tag search at scale
start = time.time()
for _ in range(100):
    conn.execute("SELECT * FROM entities WHERE list_contains(tags, 'security') AND deleted_at IS NULL").fetchall()
elapsed = time.time() - start
print(f"Tag search (100 iterations): {elapsed*10:.2f}ms avg")

# JSON field filter at scale
start = time.time()
for _ in range(100):
    conn.execute("""
        SELECT * FROM entities 
        WHERE json_extract_string(data, '$.status') = 'shipped' 
        AND deleted_at IS NULL
    """).fetchall()
elapsed = time.time() - start
print(f"JSON field filter (100 iterations): {elapsed*10:.2f}ms avg")

# ============================================================
# TEST 13: Metadata table
# ============================================================
print("\n--- TEST 13: Metadata table ---")
try:
    conn.execute("""
        CREATE TABLE metadata (
            key VARCHAR PRIMARY KEY,
            value JSON NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        INSERT INTO metadata (key, value) VALUES 
            ('schema_version', '{"version": "1.0.0"}'),
            ('entity_count', '{"count": 0}')
    """)
    result = conn.execute("SELECT * FROM metadata").fetchall()
    print(f"✅ Metadata table works: {result}")
except Exception as e:
    print(f"❌ Metadata table failed: {e}")

# ============================================================
# TEST 14: Soft delete + restore
# ============================================================
print("\n--- TEST 14: Soft delete + restore ---")
try:
    # Get an entity ID
    eid = conn.execute("SELECT id FROM entities WHERE title = 'SketchySkills'").fetchone()[0]
    
    # Soft delete
    conn.execute(f"UPDATE entities SET deleted_at = CURRENT_TIMESTAMP WHERE id = '{eid}'")
    
    # Verify hidden from normal queries
    result = conn.execute(f"SELECT title FROM entities WHERE id = '{eid}' AND deleted_at IS NULL").fetchall()
    print(f"✅ Soft deleted - hidden from queries: {result}")
    
    # Restore
    conn.execute(f"UPDATE entities SET deleted_at = NULL WHERE id = '{eid}'")
    result = conn.execute(f"SELECT title FROM entities WHERE id = '{eid}' AND deleted_at IS NULL").fetchall()
    print(f"✅ Restored: {result}")
except Exception as e:
    print(f"❌ Soft delete/restore failed: {e}")

# ============================================================
# TEST 15: Database size
# ============================================================
print("\n--- TEST 15: Database size ---")
conn.close()
size = os.path.getsize(DB_PATH)
print(f"Database size with ~2005 entities: {size / 1024:.1f} KB ({size / 1024 / 1024:.2f} MB)")

# Cleanup
os.remove(DB_PATH)
if os.path.exists(DB_PATH + ".wal"):
    os.remove(DB_PATH + ".wal")

print("\n" + "=" * 60)
print("PROTOTYPE COMPLETE")
print("=" * 60)
