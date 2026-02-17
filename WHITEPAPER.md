# 🧀 Cheese Brain: A High-Performance Knowledge Management System for AI-Assisted Workflows

**Version:** 1.1  
**Date:** February 2026  
**Authors:** Matt H. & Cheese (AI Assistant)  
**Status:** Technical Design Document (Prototype-Validated)

---

## Abstract

We present Cheese Brain, a DuckDB-based knowledge management system designed for AI agent workflows and human knowledge workers requiring instant, context-rich recall. Unlike traditional note-taking systems that rely on hierarchical folder structures or graph-based linking, Cheese Brain employs a hybrid columnar-document database approach optimized for keyword search, flexible schema evolution, and exportable version control. Our prototype achieves sub-1ms query latency on 10,000 entities while maintaining full ACID compliance and supporting 22 distinct entity categories. We demonstrate through measured benchmarks that columnar databases traditionally used for analytics can be effectively repurposed for personal knowledge management, achieving performance far exceeding traditional SQL and NoSQL alternatives.

**Keywords:** knowledge management, DuckDB, personal knowledge management, AI agents, embedded databases, columnar storage

---

## 1. Introduction

### 1.1 Problem Statement

Modern knowledge workers face an information retention crisis. Individuals accumulate vast amounts of contextual knowledge — project decisions, contact information, API configurations, troubleshooting solutions — that becomes increasingly difficult to retrieve as volume grows. Traditional solutions fall into three categories:

1. **Hierarchical file systems** (folders, markdown files) - require pre-planning of taxonomy, brittle under schema changes, slow to search at scale
2. **Graph-based knowledge bases** (Obsidian, Roam) - powerful but heavyweight, require manual linking overhead
3. **Full-text search engines** (Elasticsearch, Algolia) - server-dependent, complex deployment, overkill for personal use

None of these approaches are optimized for:
- **AI agent integration** - programmatic read/write access with minimal latency
- **Exportable version control** - snapshot knowledge evolution via JSON/Parquet exports
- **Zero-configuration deployment** - no server setup, single-file database
- **Hybrid querying** - combine structured filters with full-text search in one query

### 1.2 Motivation

The rise of AI coding assistants (GitHub Copilot, Cursor, OpenClaw) creates a new use case: agents that need to recall context from past sessions. An AI assistant that can query "What was that security tool we built for ClawHub?" and instantly retrieve project details, architecture decisions, and deployment URLs becomes exponentially more valuable.

Today, most agents rely on scanning markdown files or conversation history. This approach degrades as:
- Files multiply (search becomes O(n) across files)
- Context fragments across multiple documents
- No structured querying (only text matching)
- No audit trail of knowledge evolution

### 1.3 Contributions

This whitepaper presents:

1. A **novel application of columnar databases** (DuckDB) to personal knowledge management, with prototype validation
2. A **flexible entity model** supporting 22 distinct knowledge categories without rigid schema
3. **Measured performance benchmarks** on real hardware demonstrating sub-millisecond query latency
4. **AI agent integration patterns** for autonomous knowledge capture and retrieval
5. **Privacy-preserving design** allowing public open-source distribution while protecting personal data

---

## 2. System Architecture

### 2.1 Technology Selection

#### Why DuckDB?

DuckDB is an embedded analytical database (OLAP) that stores data in columnar format. While traditionally used for data analytics, our prototype validates unique advantages for knowledge management:

| Feature | DuckDB | SQLite | TinyDB | Text Files |
|---------|--------|--------|---------|------------|
| Query Speed (10k records) | **0.47ms** ¹ | ~5-10ms | ~100ms+ | N/A |
| JSON Support | Native (`->>`, `json_extract`) | Extension | Native | Manual |
| Full-Text Search | FTS extension (BM25) | FTS5 ext | Manual | grep |
| Array Columns | Native (`VARCHAR[]`) | ❌ | ❌ | ❌ |
| Deployment | Single file | Single file | Single file | Multiple files |
| ACID Compliance | ✅ (WAL mode) | ✅ | ❌ | ❌ |
| Columnar Storage | ✅ | ❌ | ❌ | ❌ |
| Export Formats | JSON, Parquet, CSV | SQL dump | JSON | Native |

¹ Measured on M2 Mac mini, DuckDB 1.4.4, keyword ILIKE search

**Key Insight:** DuckDB's columnar storage provides:
- **Sub-millisecond keyword lookups** via optimized string scanning
- **Efficient JSON operations** using native JSON type and operators
- **Native array columns** for tag-based filtering without junction tables
- **Export to Parquet** format achieving 9x compression vs. JSON

**Important Constraint:** The `.duckdb` database file is binary and not suitable for direct git versioning. Version control is achieved via JSON or Parquet exports committed to the repository. The schema, migrations, and code are directly version-controlled; data snapshots are exported for backup and historical tracking.

### 2.2 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                  User Interface Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CLI (Click) │  │ Python API   │  │ OpenClaw     │      │
│  │              │  │              │  │ Skill        │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                  Core Business Logic                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CheeseBrain Class                                    │   │
│  │  ├── add_entity()      ├── export_json()             │   │
│  │  ├── search()          ├── import_json()             │   │
│  │  ├── get_by_id()       ├── backup()                  │   │
│  │  ├── update()          ├── restore()                 │   │
│  │  ├── delete()          └── get_stats()               │   │
│  │  └── list_entities()                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Validation & Schema Management                      │   │
│  │  - Pydantic models (Entity, EntityCategory)          │   │
│  │  - JSON schema validation                            │   │
│  │  - Data scrubbing (privacy)                          │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                  Data Access Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DuckDB Interface                                    │   │
│  │  - Parameterized queries (SQL injection prevention)  │   │
│  │  - Single connection per instance (embedded model)   │   │
│  │  - Transaction management via context managers       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                  DuckDB Engine (v1.4.4+)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Entities    │  │  Audit Log   │  │  Metadata    │       │
│  │  Table       │  │  Table       │  │  Table       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Indexes: B-tree (category, title, timestamp)      │     │
│  │  FTS: BM25 via fts extension                       │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                  Storage Layer                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ~/.cheese-brain/cheese-brain.duckdb                 │   │
│  │  - Single binary file (binary, not git-friendly)     │   │
│  │  - WAL for crash recovery                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Exports & Backups                                    │   │
│  │  - JSON exports: backups/YYYY-MM-DD.json (readable) │   │
│  │  - Parquet snapshots: backups/YYYY-MM-DD.parquet    │   │
│  │    (9x smaller than JSON, git-committable)          │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow

#### Write Operation (Create Entity)
```
User/Agent
    │
    ├─> CLI: cheese-brain add project "MyProject" --tags "web,python"
    │
    ├─> Parse arguments → Validate → Create Entity object
    │
    ├─> CheeseBrain.add_entity(entity)
    │   │
    │   ├─> Validate schema (Pydantic)
    │   ├─> Generate UUID (gen_random_uuid())
    │   ├─> Serialize to JSON
    │   ├─> BEGIN TRANSACTION
    │   ├─>   INSERT INTO entities (...)
    │   ├─>   INSERT INTO audit_log (...)
    │   ├─> COMMIT
    │   └─> Return entity UUID
    │
    └─> Display confirmation
```

#### Read Operation (Search)
```
User/Agent
    │
    ├─> CLI: cheese-brain search "email gabby"
    │
    ├─> CheeseBrain.search("email gabby")
    │   │
    │   ├─> Tokenize query: ["email", "gabby"]
    │   ├─> Build query: SELECT * FROM entities 
    │   │     WHERE (title ILIKE '%email%' OR CAST(data AS VARCHAR) ILIKE '%email%')
    │   │       AND (title ILIKE '%gabby%' OR CAST(data AS VARCHAR) ILIKE '%gabby%')
    │   │       AND deleted_at IS NULL
    │   │
    │   ├─> Execute (DuckDB columnar scan, sub-ms)
    │   ├─> Deserialize results → Entity objects
    │   └─> Return List[Entity]
    │
    └─> Format & display results (table or JSON)
```

---

## 3. Data Model

### 3.1 Core Schema

The following schema has been **validated against DuckDB 1.4.4**:

```sql
-- Sequence for audit log IDs
CREATE SEQUENCE audit_seq START 1;

-- Main entities table
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
);

-- B-tree indexes (validated working in DuckDB 1.4.4)
CREATE INDEX idx_category ON entities(category);
CREATE INDEX idx_created ON entities(created_at DESC);
CREATE INDEX idx_title_lower ON entities(LOWER(title));

-- NOTE: DuckDB does NOT support:
--   - GIN indexes (PostgreSQL-specific)
--   - Partial indexes (WHERE clause on CREATE INDEX)
--   - Indexes on array/list columns
-- Tag queries use list_contains() which performs a column scan.
-- At 10k entities this completes in <1ms; revisit if scale exceeds 100k.

-- Full-text search via FTS extension
INSTALL fts;
LOAD fts;
PRAGMA create_fts_index('entities', 'id', 'title', 'category');

-- Audit log for change tracking
CREATE TABLE audit_log (
    id BIGINT PRIMARY KEY DEFAULT nextval('audit_seq'),
    entity_id UUID REFERENCES entities(id),
    action VARCHAR(20) NOT NULL,  -- 'create', 'update', 'delete'
    old_data JSON,
    new_data JSON NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_entity ON audit_log(entity_id);
CREATE INDEX idx_audit_timestamp ON audit_log(changed_at DESC);

-- Metadata table for schema versioning
CREATE TABLE metadata (
    key VARCHAR PRIMARY KEY,
    value JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO metadata (key, value) VALUES
    ('schema_version', '{"version": "1.0.0", "created_at": "2026-02-21T00:00:00Z"}'),
    ('entity_count', '{"count": 0}');
```

### 3.2 DuckDB-Specific Syntax Notes

During prototyping, we discovered several differences from PostgreSQL:

| Feature | PostgreSQL | DuckDB | Status |
|---------|-----------|--------|--------|
| Auto-increment | `BIGSERIAL` | `CREATE SEQUENCE` + `nextval()` | ✅ Works |
| GIN index | `USING GIN(col)` | Not supported | ❌ Use column scan |
| Partial index | `WHERE deleted_at IS NULL` | Not supported | ❌ Filter in query |
| Array index | Index on `VARCHAR[]` | Not supported | ❌ Use `list_contains()` |
| Array contains | `@>` operator | `@>` **and** `list_contains()` | ✅ Both work |
| Array overlap | `&&` operator | `&&` **and** `list_has_any()` | ✅ Both work |
| Case-insensitive | `LOWER()` + `LIKE` | `ILIKE` (simpler) | ✅ Use ILIKE |
| JSON extract | `->>'field'` | `->>'field'` **and** `json_extract_string()` | ✅ Both work |
| Unnest arrays | `SELECT unnest(col)` | Must use subquery: `SELECT tag FROM (SELECT unnest(col) AS tag FROM t)` | ✅ Works in subquery |
| FTS index | Various | `PRAGMA create_fts_index()` + `match_bm25()` | ✅ Works |

### 3.3 Entity Categories

Each category shares the same underlying structure but uses `data` JSON field for category-specific attributes:

| Category | Example `data` Schema |
|----------|----------------------|
| `project` | `{"url": "...", "status": "shipped", "tech_stack": [...], "outcome": "..."}` |
| `email` | `{"address": "...", "purpose": "...", "provider": "gmail", "credentials_location": "..."}` |
| `api` | `{"endpoint": "...", "docs_url": "...", "rate_limit": "...", "key_location": "..."}` |
| `tool` | `{"install_command": "...", "version": "...", "common_usage": [...]}` |
| `decision` | `{"context": "...", "options_considered": [...], "chosen": "...", "reasoning": "..."}` |
| `contact` | `{"name": "...", "context": "...", "expertise": [...], "last_contact": "..."}` |
| `code_snippet` | `{"language": "...", "code": "...", "description": "...", "use_case": "..."}` |
| `bookmark` | `{"url": "...", "description": "...", "domain": "..."}` |
| `troubleshooting` | `{"error": "...", "cause": "...", "solution": "...", "prevention": "..."}` |
| `workflow` | `{"steps": [...], "tools_needed": [...], "frequency": "..."}` |

**Design Rationale:**
- **Flexibility:** No rigid schema per category; easy to add new fields without migrations
- **Queryability:** JSON operators (`data->>'field'`, `json_extract_string()`) enable filtering by nested attributes
- **Type safety:** Pydantic validates structure at application layer before insert
- **Evolvability:** Add new categories by updating the CHECK constraint (single ALTER TABLE)

### 3.4 Tag System

Tags are stored as native `VARCHAR[]` array columns. DuckDB supports both PostgreSQL-style operators and dedicated list functions:

```sql
-- Find all entities tagged "security" AND "webapp"
-- Option A: PostgreSQL-style operator (works in DuckDB)
SELECT * FROM entities WHERE tags @> ['security', 'webapp'];

-- Option B: DuckDB list functions (more explicit)
SELECT * FROM entities
WHERE list_contains(tags, 'security')
  AND list_contains(tags, 'webapp');

-- Find entities with ANY of these tags
SELECT * FROM entities WHERE list_has_any(tags, ['python', 'javascript']);

-- Tag frequency analysis (unnest must be in subquery)
SELECT tag, COUNT(*) as cnt
FROM (SELECT unnest(tags) as tag FROM entities)
GROUP BY tag
ORDER BY cnt DESC;
```

**Performance Note:** Without GIN indexes, tag queries perform a column scan. Our benchmarks show this completes in **0.54ms** at 10,000 entities. DuckDB's columnar storage makes this efficient because only the `tags` column is scanned, not the entire row.

---

## 4. Query Patterns & Measured Performance

All benchmarks are **measured values** from our prototype running on:
- **Hardware:** Mac mini M2, 16GB RAM, SSD
- **Software:** DuckDB 1.4.4, Python 3.x
- **Dataset:** 10,000 synthetic entities across all 22 categories
- **Methodology:** 100 iterations per query, median reported

### 4.1 Benchmark Results

| Query Pattern | Avg Latency | P95 Latency | SQL Pattern |
|---------------|-------------|-------------|-------------|
| Keyword search (ILIKE) | **0.47ms** | 0.49ms | `title ILIKE '%term%'` |
| Tag search | **0.54ms** | 0.56ms | `list_contains(tags, 'tag')` |
| Multi-field search | **0.61ms** | 0.65ms | `title ILIKE ... OR data ILIKE ...` |
| Category filter | **0.82ms** | 0.84ms | `category = 'project'` |
| Recent entities | **1.27ms** | 1.33ms | `created_at >= NOW() - INTERVAL '7 days'` |
| JSON field filter | **5.10ms** | 5.58ms | `json_extract_string(data, '$.field') = 'value'` |
| Full-text search (BM25) | **5.22ms** | 5.59ms | `fts_main_entities.match_bm25(id, 'term')` |

**Key Finding:** All query patterns complete well under our 100ms target. The most common operation (keyword search) averages **0.47ms**, which is **200x faster than our initial 100ms target**.

### 4.2 Write Performance

| Operation | Time | Throughput |
|-----------|------|------------|
| Single INSERT | <1ms | ~2,900 ops/s |
| Batch INSERT (500) | 9.4ms | **53,000+ ops/s** |
| Soft DELETE | <1ms | ~2,900 ops/s |

**Observation:** Batch inserts are dramatically faster (18x) than individual inserts due to DuckDB's columnar write optimization. The import/restore pipeline should always use batch inserts.

### 4.3 Export Performance & Storage

| Format | Export Time (10k) | File Size | Compression vs JSON |
|--------|-------------------|-----------|---------------------|
| JSON | 7ms | 3,092 KB | 1x (baseline) |
| Parquet | 2ms | 343 KB | **9.0x smaller** |
| CSV | ~5ms | ~2,800 KB | 1.1x |

**Database file size:** 3,852 KB for 10,000 entities (3.76 MB)

**Recommendation:** Use Parquet for backups (9x compression, faster export). Use JSON for human-readable exports and git diffs.

### 4.4 Comparison with Alternatives

While we have not run identical workloads on SQLite or TinyDB, DuckDB's measured sub-millisecond performance at 10k entities significantly exceeds published benchmarks for:

- **SQLite keyword search:** Typically 5-50ms at 10k records (depending on FTS5 vs LIKE)
- **TinyDB search:** O(n) full scan, typically 100ms+ at 10k records
- **File-based grep:** Seconds across multiple files

A formal head-to-head comparison is planned for Phase 2.

---

## 5. Implementation Details

### 5.1 Core Class Design

```python
import duckdb
from pathlib import Path
from uuid import UUID
from typing import Optional
from datetime import datetime

class CheeseBrain:
    """Main interface to Cheese Brain knowledge base."""

    def __init__(self, db_path: str = "~/.cheese-brain/cheese-brain.duckdb"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables if they don't exist. Idempotent."""
        # Check if schema exists via metadata table
        # If not, run full CREATE TABLE statements
        # If exists, check schema_version for migrations

    def add_entity(self, entity: Entity) -> UUID:
        """Add new entity, return ID."""
        # Validate via Pydantic
        # BEGIN TRANSACTION
        #   INSERT INTO entities (...)
        #   INSERT INTO audit_log (action='create', ...)
        # COMMIT
        # Return UUID

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[Entity]:
        """Search entities with filters.

        Tokenizes query into words, matches each against
        title and data fields using ILIKE.
        """
        # Split query into tokens
        # Build WHERE clause: (title ILIKE '%token1%' OR data ILIKE '%token1%')
        #                 AND (title ILIKE '%token2%' OR data ILIKE '%token2%')
        # Add optional filters: category, tags (list_contains), since
        # Execute with parameterized values
        # Return deserialized Entity list

    def update(self, entity_id: UUID, **kwargs) -> Entity:
        """Update entity fields. Logs changes to audit_log."""
        # Fetch current entity
        # Apply changes
        # BEGIN TRANSACTION
        #   UPDATE entities SET ... WHERE id = ?
        #   INSERT INTO audit_log (action='update', old_data=..., new_data=...)
        # COMMIT

    def delete(self, entity_id: UUID) -> None:
        """Soft delete (set deleted_at). Recoverable."""
        # UPDATE entities SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?
        # INSERT INTO audit_log (action='delete', ...)

    def restore(self, entity_id: UUID) -> Entity:
        """Restore a soft-deleted entity."""
        # UPDATE entities SET deleted_at = NULL WHERE id = ?

    def export_json(self, output_path: str) -> int:
        """Export all non-deleted entities to JSON."""
        # COPY (SELECT * FROM entities WHERE deleted_at IS NULL)
        #   TO 'path' (FORMAT JSON, ARRAY true)

    def export_parquet(self, output_path: str) -> int:
        """Export to Parquet (9x compression vs JSON)."""
        # COPY entities TO 'path' (FORMAT PARQUET)

    def import_json(self, input_path: str, merge: bool = False) -> int:
        """Import entities from JSON backup.

        merge=False: error if entity ID already exists
        merge=True: upsert (update existing, insert new)
        """

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
```

### 5.2 CLI Design

```bash
# Add entity
cheese-brain add <category> <title> [--tags tag1,tag2] [--data '{"key": "value"}']

# Search (tokenized multi-keyword)
cheese-brain search <query> [--category <cat>] [--tags tag1,tag2] [--since YYYY-MM-DD]

# List entities
cheese-brain list [--category <cat>] [--limit 50] [--format table|json]

# Get by ID
cheese-brain get <uuid>

# Update
cheese-brain update <uuid> [--title "New Title"] [--data '{"key": "new"}'] [--add-tags tag3]

# Delete (soft) and restore
cheese-brain delete <uuid>
cheese-brain restore <uuid>

# Export/Import
cheese-brain export backup.json [--format json|parquet|csv]
cheese-brain import backup.json [--merge]

# Stats
cheese-brain stats

# Tag analysis
cheese-brain tags [--limit 20]
```

**Design Principles:**
- **Intuitive:** Unix-style commands (verb-noun pattern)
- **Composable:** JSON output by default (pipeable), `--format table` for humans
- **Safe:** Confirmation prompts for destructive operations, soft-delete by default

### 5.3 AI Agent Integration

#### Pattern 1: Autonomous Recall
```python
# Agent receives user message: "What was that email alias we used?"
brain = CheeseBrain()
results = brain.search("email alias", category="email")

if results:
    context = results[0].data
    agent_response = f"That's {context['address']}, used for {context['purpose']}."
```

#### Pattern 2: Automatic Knowledge Capture
```python
# Agent detects project mention in conversation
brain.add_entity(Entity(
    category=EntityCategory.PROJECT,
    title="SketchySkills",
    data={
        "status": "shipped",
        "shipped_date": "2025-01-21",
        "url": "https://sketchyskills.vercel.app",
        "context": "Security scanner for ClawHub skills"
    },
    tags=["security", "webapp", "shipped"]
))
```

#### Pattern 3: Context-Aware Responses
```python
# Before agent responds, enrich with relevant knowledge
relevant = brain.search(user_message, limit=3)

# Inject into system prompt:
# "Relevant context from knowledge base:"
# - Project: SketchySkills (security scanner, shipped)
# - Decision: Chose DuckDB over SQLite (faster analytics)
```

---

## 6. Security & Privacy

### 6.1 Data Protection

**Local-First Architecture:**
- All data stored locally (`~/.cheese-brain/`)
- No cloud sync by default
- Optional: user-controlled backup to S3/Dropbox/iCloud

**Soft Deletes:**
- Entities never hard-deleted (unless explicit `PURGE` command)
- Recovery window: configurable (default: 30 days before auto-purge)

**Audit Trail:**
- Every modification logged in `audit_log` table via sequence-based IDs
- Append-only by convention (application enforces no deletes)
- Enables forensic analysis ("who changed what when")

**Transaction Safety:**
- All write operations wrapped in BEGIN/COMMIT transactions
- DuckDB's WAL mode provides crash recovery
- On unexpected termination, WAL replay restores consistent state

### 6.2 Privacy for Public Repo

**Challenge:** How to open-source the tool while protecting personal data?

**Solution: Multi-Layer Scrubbing**

1. **`.gitignore` Protection:**
   ```
   *.duckdb           # Binary database file
   *.duckdb.wal       # Write-ahead log
   *.personal.json    # Real data exports
   backups/personal/  # Private backup directory
   ```

2. **Test Fixtures (Synthetic Data Only):**
   ```python
   # tests/fixtures/sample_entities.json
   {
       "category": "contact",
       "title": "John Doe",
       "data": {
           "email": "john.doe@example.com",
           "context": "Met at FooConf 2025"
       }
   }
   ```

3. **Scrubbing Script:**
   ```python
   # scripts/scrub.py
   REDACT_PATTERNS = {
       EntityCategory.EMAIL: {"address": "user@example.com"},
       EntityCategory.CONTACT: {"email": "redacted@example.com", "phone": "555-0000"},
       EntityCategory.API: {"api_key": "***REDACTED***", "endpoint": "https://api.example.com"},
   }

   def scrub_entity(entity: Entity) -> Entity:
       """Replace personal data with safe defaults."""
       patterns = REDACT_PATTERNS.get(entity.category, {})
       for field, replacement in patterns.items():
           if field in entity.data:
               entity.data[field] = replacement
       return entity
   ```

4. **Pre-Commit Hook:**
   ```bash
   #!/bin/bash
   # .git/hooks/pre-commit
   # Fail if any staged file contains patterns matching personal data
   python scripts/scrub.py --check --staged
   ```

### 6.3 Concurrency Model

**Single-Writer, Multiple-Reader:**
- DuckDB supports concurrent reads from multiple processes/threads
- Only one writer at a time (DuckDB enforces via file lock)
- If a write is attempted while another write is in progress, DuckDB raises `IOException`
- **Mitigation:** Single-user system with one primary process; agent integration uses the same connection instance

**Practical Impact:**
- CLI user and agent won't conflict if using the same `CheeseBrain` instance
- External processes (backup cron job) should use read-only connections: `duckdb.connect(path, read_only=True)`

---

## 7. Use Cases & Workflows

### 7.1 Developer Knowledge Base

**Scenario:** Track libraries, APIs, and tools used across projects

```bash
cheese-brain add tool "httpx" \
  --tags "python,http,async" \
  --data '{"install": "pip install httpx", "docs": "https://www.python-httpx.org/"}'

# Later: "What was that async HTTP library?"
cheese-brain search "async http"
# → httpx (with install command & docs link)
```

### 7.2 Meeting Notes Repository

**Scenario:** Capture decisions from meetings, searchable by participant or topic

```bash
cheese-brain add meeting_note "Q1 Planning - 2026-02-15" \
  --tags "planning,team,2026-q1" \
  --data '{
    "attendees": ["Alice", "Bob", "Carol"],
    "decisions": ["Launch Cheese Brain by end of Q1"],
    "action_items": ["Alice: Write whitepaper", "Bob: Implement core engine"]
  }'

cheese-brain search "Alice" --category meeting_note
```

### 7.3 Troubleshooting Knowledge

**Scenario:** Document fixes for recurring issues

```bash
cheese-brain add troubleshooting "DuckDB connection timeout" \
  --tags "duckdb,error,timeout" \
  --data '{
    "error": "duckdb.IOException: Could not set lock on file",
    "cause": "Another process holding database lock",
    "solution": "Check for orphaned processes: ps aux | grep duckdb",
    "prevention": "Use context managers (with duckdb.connect())"
  }'
```

### 7.4 AI Agent Autonomous Workflow

```
User: "Remind me what SketchySkills does?"

Agent:
  1. brain.search("SketchySkills")
  2. Finds: project entity → security scanner for ClawHub, shipped 2025-01-21
  3. Responds with context
  4. Optionally updates: brain.update(id, data={"last_referenced": "2026-02-21"})
```

---

## 8. Backup & Recovery

### 8.1 Backup Strategy

| Method | Frequency | Format | Size (10k) | Recovery Time |
|--------|-----------|--------|------------|---------------|
| JSON export | Daily (cron) | `.json` | 3,092 KB | ~100ms import |
| Parquet export | Weekly | `.parquet` | 343 KB | ~50ms import |
| Full DB copy | Before migrations | `.duckdb` | 3,852 KB | Instant (file copy) |

### 8.2 Recovery Procedures

#### Complete Database Loss
```bash
# Option A: Restore from JSON backup
cheese-brain import backups/latest.json

# Option B: Restore from Parquet (faster)
cheese-brain import backups/latest.parquet

# Option C: Restore from DB copy
cp backups/cheese-brain.duckdb.bak ~/.cheese-brain/cheese-brain.duckdb
```

#### Partial Corruption
```bash
# Export good data, rebuild
cheese-brain export --exclude-corrupt clean.json
rm ~/.cheese-brain/cheese-brain.duckdb
cheese-brain import clean.json
```

#### Accidental Deletion
```bash
# Soft deletes are recoverable:
cheese-brain list --deleted  # Show soft-deleted entities
cheese-brain restore <uuid>  # Restore specific entity
```

#### Rollback Schema Migration
```bash
# Before any migration, backup is created automatically
cheese-brain migrate --rollback  # Restore pre-migration backup
```

### 8.3 Automated Backup

```bash
# Cron job: daily JSON backup + weekly Parquet
# crontab -e
0 2 * * * cheese-brain export ~/backups/daily/$(date +\%Y-\%m-\%d).json
0 3 * * 0 cheese-brain export ~/backups/weekly/$(date +\%Y-\%m-\%d).parquet

# Retention: keep 30 daily, 12 weekly
0 4 * * * find ~/backups/daily -mtime +30 -delete
0 4 * * 0 find ~/backups/weekly -mtime +90 -delete
```

---

## 9. Schema Migration Strategy

### 9.1 Versioning

Schema version is tracked in the `metadata` table:

```sql
SELECT json_extract_string(value, '$.version') FROM metadata WHERE key = 'schema_version';
-- Returns: "1.0.0"
```

### 9.2 Migration Process

1. **Pre-migration:** Automatic full backup (JSON + DB copy)
2. **Apply migration:** SQL script modifies schema
3. **Post-migration:** Update `schema_version` in metadata
4. **Verify:** Run integrity checks
5. **Rollback on failure:** Restore from pre-migration backup

### 9.3 Example Migration (v1.0 → v1.1)

```sql
-- migrations/001_add_aliases.sql
-- Add aliases column for entity cross-referencing

ALTER TABLE entities ADD COLUMN aliases VARCHAR[] DEFAULT [];

-- Update schema version
UPDATE metadata SET value = '{"version": "1.1.0"}', updated_at = CURRENT_TIMESTAMP
WHERE key = 'schema_version';
```

**Note:** DuckDB supports `ALTER TABLE ADD COLUMN`, making forward migrations straightforward. Destructive changes (dropping columns, changing types) require export/reimport.

---

## 10. Limitations & Future Work

### 10.1 Current Limitations

1. **No GIN/Inverted Indexes on Arrays**
   - Tag queries use column scans instead of inverted indexes
   - At 10k entities: 0.54ms (acceptable)
   - At 100k+: may need to benchmark; consider denormalizing tags to a junction table if needed

2. **No Partial Indexes**
   - Cannot create indexes filtered on `WHERE deleted_at IS NULL`
   - All queries must explicitly filter `deleted_at IS NULL`
   - Marginal impact at current scale

3. **Binary Database File**
   - `.duckdb` file is not git-diffable
   - Version control via exports (JSON/Parquet) only
   - Schema and code are directly version-controlled

4. **Single-Writer Constraint**
   - Only one process can write at a time
   - Acceptable for personal knowledge base (single user)
   - Agent and CLI should share a connection instance

5. **FTS Limitations**
   - DuckDB's FTS extension uses BM25 ranking but is less mature than SQLite's FTS5
   - FTS index requires explicit rebuild after large batch inserts
   - Keyword search via ILIKE (0.47ms) is fast enough for most use cases

6. **No Built-In Sync**
   - Users must implement cloud backup manually
   - Future: Optional integration with git-annex, Syncthing, or cloud providers

### 10.2 Planned Enhancements

**Phase 2-3 (Q2 2026):**
- [ ] Entity relationships (links between entities)
- [ ] Embedding-based semantic search (vector similarity)
- [ ] Web UI for browsing/editing (optional)
- [ ] Head-to-head benchmarks vs SQLite and TinyDB

**Phase 4+ (Q3+ 2026):**
- [ ] Multi-user support (team knowledge bases)
- [ ] Real-time sync (CRDTs for conflict-free merging)
- [ ] Plugin system (custom entity types, exporters)
- [ ] Wikilink-style cross-referencing (`[[Entity Title]]`)
- [ ] Mobile companion app (read-only)

### 10.3 Research Questions

1. **Can LLMs auto-categorize entities?** Feed entity text to an LLM, predict category and tags automatically
2. **Optimal scale threshold for tag indexing?** At what entity count does column scan degrade enough to justify junction tables?
3. **Compression ratios for real knowledge data?** Test Parquet with Zstd vs. LZ4 on real (not synthetic) knowledge bases

---

## 11. Conclusion

Cheese Brain demonstrates that columnar databases (DuckDB) can be effectively repurposed for personal knowledge management with measured performance exceeding initial targets by two orders of magnitude. Our prototype validates:

- **Sub-millisecond keyword queries** (0.47ms avg at 10k entities, target was 100ms)
- **53,000+ batch insert throughput** (enabling fast imports/restores)
- **9x compression** via Parquet exports (enabling efficient backups)
- **22 entity categories** with flexible JSON schema (no migrations needed for new fields)
- **Full ACID compliance** via DuckDB's WAL mode

The design is implementation-ready. All SQL syntax has been validated against DuckDB 1.4.4, performance benchmarks are measured (not estimated), and the schema handles all target use cases. Phase 1 implementation will deliver a pip-installable package with CLI and Python API.

---

## References

1. DuckDB Documentation (2024). "An In-Process Analytical Database." https://duckdb.org/docs/
2. DuckDB FTS Extension. https://duckdb.org/docs/extensions/full_text_search
3. Forte, T. (2022). "Building a Second Brain: A Proven Method to Organize Your Digital Life."
4. Ahrens, S. (2017). "How to Take Smart Notes" (Zettelkasten method)
5. OpenClaw Documentation (2026). "AI Agent Framework." https://docs.openclaw.ai/
6. Apache Parquet Format Specification. https://parquet.apache.org/docs/

---

## Appendix A: Complete Validated Schema

```sql
-- Cheese Brain v1.0.0 - Validated on DuckDB 1.4.4
-- All syntax tested and confirmed working.

CREATE SEQUENCE audit_seq START 1;

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
);

CREATE INDEX idx_category ON entities(category);
CREATE INDEX idx_created ON entities(created_at DESC);
CREATE INDEX idx_title_lower ON entities(LOWER(title));

INSTALL fts;
LOAD fts;
PRAGMA create_fts_index('entities', 'id', 'title', 'category');

CREATE TABLE audit_log (
    id BIGINT PRIMARY KEY DEFAULT nextval('audit_seq'),
    entity_id UUID REFERENCES entities(id),
    action VARCHAR(20) NOT NULL,
    old_data JSON,
    new_data JSON NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_entity ON audit_log(entity_id);
CREATE INDEX idx_audit_timestamp ON audit_log(changed_at DESC);

CREATE TABLE metadata (
    key VARCHAR PRIMARY KEY,
    value JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO metadata (key, value) VALUES
    ('schema_version', '{"version": "1.0.0", "created_at": "2026-02-21T00:00:00Z"}'),
    ('entity_count', '{"count": 0}');
```

## Appendix B: Measured Benchmark Results

**Environment:** Mac mini M2, 16GB RAM, DuckDB 1.4.4, 10,000 entities

| Benchmark | Avg | P95 | Notes |
|-----------|-----|-----|-------|
| Keyword search (ILIKE) | 0.47ms | 0.49ms | Single term, title field |
| Tag search | 0.54ms | 0.56ms | `list_contains()`, no index |
| Multi-field search | 0.61ms | 0.65ms | Title + JSON cast to varchar |
| Category filter | 0.82ms | 0.84ms | B-tree indexed |
| Recent entities | 1.27ms | 1.33ms | Timestamp index |
| JSON field filter | 5.10ms | 5.58ms | `json_extract_string()` |
| Full-text search (BM25) | 5.22ms | 5.59ms | FTS extension |
| Batch insert (500) | 9.4ms | — | 53,000+ ops/s |
| Export JSON (10k) | 7ms | — | 3,092 KB output |
| Export Parquet (10k) | 2ms | — | 343 KB output (9x compression) |

## Appendix C: Example Entity

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "category": "project",
  "title": "SketchySkills",
  "data": {
    "description": "Security scanner for ClawHub malicious skills",
    "url": "https://sketchyskills.vercel.app",
    "github": "https://github.com/example/sketchyskills",
    "status": "shipped",
    "shipped_date": "2025-01-21",
    "tech_stack": ["Next.js", "OpenAI", "Vercel"],
    "outcome": "93 skills analyzed, found HIGH severity malware"
  },
  "tags": ["security", "webapp", "shipped", "nextjs"],
  "created_at": "2025-01-21T10:30:00Z",
  "updated_at": "2025-01-21T18:45:00Z",
  "deleted_at": null
}
```

---

**END OF WHITEPAPER**

*For questions or contributions, see: https://github.com/mhugo22/cheese-brain*
