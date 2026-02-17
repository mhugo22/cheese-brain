#!/usr/bin/env python3
"""Scale test - 10k entities for realistic benchmarks."""

import duckdb
import time
import os
import json

DB_PATH = "/tmp/cheese-brain-scale.duckdb"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = duckdb.connect(DB_PATH)

# Create schema
conn.execute("""
    CREATE TABLE entities (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        category VARCHAR NOT NULL,
        title VARCHAR(500) NOT NULL,
        data JSON NOT NULL,
        tags VARCHAR[] DEFAULT [],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        deleted_at TIMESTAMP
    )
""")
conn.execute("CREATE INDEX idx_category ON entities(category)")
conn.execute("CREATE INDEX idx_created ON entities(created_at DESC)")
conn.execute("CREATE INDEX idx_title_lower ON entities(LOWER(title))")

categories = ['project', 'email', 'api', 'tool', 'decision', 'code_snippet',
              'contact', 'bookmark', 'config_location', 'failed_experiment',
              'problem', 'learning_note', 'workflow', 'troubleshooting',
              'infrastructure', 'meeting_note', 'idea', 'habit', 'dependency',
              'environment_config', 'vendor_license', 'metric']

# Bulk insert 10k entities
print("Inserting 10,000 entities...")
start = time.time()
batch_size = 500
for batch in range(20):
    values = []
    for i in range(batch_size):
        idx = batch * batch_size + i
        cat = categories[idx % len(categories)]
        tags = [f"tag-{idx % 50}", f"cat-{cat}", "test"]
        tags_str = str(tags).replace("'", "'")
        data = json.dumps({"index": idx, "desc": f"Entity number {idx}", "status": "active" if idx % 3 == 0 else "archived"})
        values.append(f"('{cat}', 'Entity-{cat}-{idx}', '{data}', {tags_str})")
    conn.execute(f"INSERT INTO entities (category, title, data, tags) VALUES {','.join(values)}")

elapsed = time.time() - start
count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
print(f"✅ Inserted {count} entities in {elapsed:.3f}s ({count/elapsed:.0f} ops/s)")

# Install FTS
conn.execute("INSTALL fts; LOAD fts;")
conn.execute("PRAGMA create_fts_index('entities', 'id', 'title', 'category')")

print(f"\n--- Benchmarks at {count} entities ---\n")

# 1. Keyword search (ILIKE)
times = []
for _ in range(100):
    s = time.time()
    conn.execute("SELECT * FROM entities WHERE title ILIKE '%Entity-project-500%' AND deleted_at IS NULL").fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"Keyword search (ILIKE):     avg={avg:.2f}ms  p95={p95:.2f}ms")

# 2. Category filter
times = []
for _ in range(100):
    s = time.time()
    conn.execute("SELECT * FROM entities WHERE category = 'project' AND deleted_at IS NULL").fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"Category filter:            avg={avg:.2f}ms  p95={p95:.2f}ms")

# 3. Tag search
times = []
for _ in range(100):
    s = time.time()
    conn.execute("SELECT * FROM entities WHERE list_contains(tags, 'tag-25') AND deleted_at IS NULL").fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"Tag search (list_contains): avg={avg:.2f}ms  p95={p95:.2f}ms")

# 4. JSON field filter
times = []
for _ in range(100):
    s = time.time()
    conn.execute("""
        SELECT * FROM entities 
        WHERE json_extract_string(data, '$.status') = 'active' 
        AND deleted_at IS NULL
    """).fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"JSON field filter:          avg={avg:.2f}ms  p95={p95:.2f}ms")

# 5. FTS search
times = []
for _ in range(100):
    s = time.time()
    conn.execute("""
        SELECT title, fts_main_entities.match_bm25(id, 'project') as score
        FROM entities WHERE score IS NOT NULL ORDER BY score DESC LIMIT 10
    """).fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"Full-text search (BM25):    avg={avg:.2f}ms  p95={p95:.2f}ms")

# 6. Multi-keyword search across title + JSON
times = []
for _ in range(100):
    s = time.time()
    conn.execute("""
        SELECT * FROM entities 
        WHERE (title ILIKE '%project%' OR CAST(data AS VARCHAR) ILIKE '%active%')
        AND deleted_at IS NULL LIMIT 50
    """).fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"Multi-field search:         avg={avg:.2f}ms  p95={p95:.2f}ms")

# 7. Recent entities
times = []
for _ in range(100):
    s = time.time()
    conn.execute("""
        SELECT * FROM entities 
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
        AND deleted_at IS NULL
        ORDER BY created_at DESC LIMIT 50
    """).fetchall()
    times.append(time.time() - s)
avg = sum(times) / len(times) * 1000
p95 = sorted(times)[94] * 1000
print(f"Recent entities:            avg={avg:.2f}ms  p95={p95:.2f}ms")

# 8. Export benchmark
start = time.time()
conn.execute("COPY entities TO '/tmp/cheese-brain-10k.json' (FORMAT JSON, ARRAY true)")
elapsed = time.time() - start
json_size = os.path.getsize('/tmp/cheese-brain-10k.json')
print(f"\nExport 10k to JSON:         {elapsed:.3f}s ({json_size/1024:.0f} KB)")

start = time.time()
conn.execute("COPY entities TO '/tmp/cheese-brain-10k.parquet' (FORMAT PARQUET)")
elapsed = time.time() - start
parquet_size = os.path.getsize('/tmp/cheese-brain-10k.parquet')
print(f"Export 10k to Parquet:      {elapsed:.3f}s ({parquet_size/1024:.0f} KB)")

# 9. Tag frequency (unnest alternative)
try:
    start = time.time()
    result = conn.execute("""
        SELECT tag, COUNT(*) as cnt
        FROM (SELECT unnest(tags) as tag FROM entities)
        GROUP BY tag ORDER BY cnt DESC LIMIT 10
    """).fetchall()
    elapsed = time.time() - start
    print(f"\nTag frequency (subquery unnest): {elapsed*1000:.2f}ms")
    print(f"  Top tags: {result[:5]}")
except Exception as e:
    print(f"❌ unnest in subquery failed: {e}")
    # Try LATERAL
    try:
        result = conn.execute("""
            SELECT t.tag, COUNT(*) as cnt
            FROM entities, LATERAL unnest(entities.tags) AS t(tag)
            GROUP BY t.tag ORDER BY cnt DESC LIMIT 10
        """).fetchall()
        print(f"  ✅ LATERAL unnest works: {result[:5]}")
    except Exception as e2:
        print(f"  ❌ LATERAL also failed: {e2}")

# DB size
conn.close()
db_size = os.path.getsize(DB_PATH)
print(f"\nDB size (10k entities):     {db_size/1024:.0f} KB ({db_size/1024/1024:.2f} MB)")
print(f"JSON export size:           {json_size/1024:.0f} KB")
print(f"Parquet export size:        {parquet_size/1024:.0f} KB")
print(f"Parquet compression ratio:  {json_size/parquet_size:.1f}x vs JSON")

# Cleanup
for f in [DB_PATH, DB_PATH + ".wal", '/tmp/cheese-brain-10k.json', '/tmp/cheese-brain-10k.parquet']:
    if os.path.exists(f):
        os.remove(f)

print("\n✅ Scale test complete")
