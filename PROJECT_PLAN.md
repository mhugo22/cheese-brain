# 🧀 Cheese Brain - Project Plan

**Status:** Planning → Implementation  
**Repository:** https://github.com/mhugo22/cheese-brain (to be created)  
**Vision:** Production-grade DuckDB-based knowledge management system for agent-assisted recall and context tracking

---

## 🎯 Project Objectives

### Primary Goals
1. **Fast keyword-based retrieval** - Look up projects, contacts, configs, decisions instantly
2. **Git-friendly storage** - Version control for knowledge evolution
3. **Flexible schema** - Support 22+ entity types without rigid structure
4. **Agent-optimized** - Cheese can query/update autonomously
5. **Public & reusable** - Clean, documented, ready for others to fork

### Success Metrics
- Query response time: <100ms for keyword lookups
- Import/export: full data backup/restore in <10 seconds
- Agent integration: seamless read/write from OpenClaw sessions
- Test coverage: 100% of core CRUD operations
- Documentation: complete enough for external contributors

---

## 📋 Requirements

### Functional Requirements

#### Entity Types (All Supported)
1. Project History
2. Email Accounts/Aliases
3. External Services/APIs
4. Tools/CLIs
5. Past Decisions
6. Code Patterns/Snippets
7. Contacts/People
8. Links/Bookmarks
9. Credentials/Config Locations
10. Failed Experiments
11. Problems/Challenges List
12. Learning Notes/Research
13. Workflows/Procedures
14. Troubleshooting Solutions
15. Infrastructure/Systems
16. Meeting Notes
17. Ideas/Future Work
18. Habits/Recurring Events
19. Dependencies/Relationships
20. Environment Configs
21. Vendor/License Info
22. Personal Metrics

#### Core Operations
- **Create** - Add new entities with metadata (tags, timestamps, category)
- **Read** - Query by keyword, category, date range, tags
- **Update** - Modify existing entities, track revision history
- **Delete** - Soft delete with archive/recovery option
- **Export** - Full data dump to JSON/CSV/SQL for backup
- **Import** - Restore from backup, merge external data
- **Search** - Full-text search across all fields

### Non-Functional Requirements
- **Performance** - Sub-100ms queries on 10k+ records
- **Privacy** - No personal data in public repo (scrubbed test fixtures)
- **Portability** - Works on macOS/Linux/Windows with Python 3.9+
- **Extensibility** - Plugin system for custom entity types
- **Documentation** - Full API docs, architecture diagrams, tutorials

---

## 🏗️ Architecture

### Technology Stack
- **Database:** DuckDB 1.1+ (embedded analytics engine)
- **Language:** Python 3.9+ (CLI + library)
- **Testing:** pytest + hypothesis (property-based testing)
- **Docs:** Mermaid diagrams + Markdown
- **CI/CD:** GitHub Actions (test + lint on push)

### Data Model

```sql
-- Core entities table (flexible JSON schema)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR NOT NULL,  -- e.g., 'project', 'contact', 'tool'
    title VARCHAR NOT NULL,
    data JSON NOT NULL,          -- Flexible schemaless storage
    tags VARCHAR[],              -- Array of keywords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP         -- Soft delete
);

-- Full-text search virtual table
CREATE INDEX idx_title_fts ON entities USING GIN(title);
CREATE INDEX idx_tags ON entities(tags);
CREATE INDEX idx_category ON entities(category);

-- Audit log for tracking changes
CREATE TABLE audit_log (
    id BIGINT PRIMARY KEY,
    entity_id UUID REFERENCES entities(id),
    action VARCHAR,  -- 'create', 'update', 'delete'
    old_data JSON,
    new_data JSON,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### System Architecture

```
┌─────────────────────────────────────────────┐
│           User / Agent Interface            │
│  (CLI, Python API, OpenClaw Integration)   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Cheese Brain Core Library           │
│  - Query Engine                             │
│  - CRUD Operations                          │
│  - Import/Export                            │
│  - Validation & Schema Management           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            DuckDB Engine                    │
│  - entities table (JSON + arrays)           │
│  - audit_log (change tracking)              │
│  - Full-text indexes                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Storage Layer                      │
│  - cheese-brain.duckdb (local file)        │
│  - Backups (JSON/Parquet exports)          │
│  - Git repository (schema + migrations)    │
└─────────────────────────────────────────────┘
```

---

## 🧪 Testing Strategy

### Unit Tests
- **CRUD operations** - Create/Read/Update/Delete for each entity type
- **Query validation** - Keyword search, filters, date ranges
- **Schema validation** - Reject malformed data
- **Export/Import** - Round-trip data integrity

### Integration Tests
- **Full workflow** - Import fixture → query → update → export → verify
- **Concurrent access** - Multiple readers/writers (within DuckDB limits)
- **Error handling** - Corrupt DB recovery, missing files

### Performance Benchmarks
- **Query latency** - 100, 1k, 10k, 100k records
- **Import speed** - Large JSON/CSV datasets
- **Disk usage** - Storage efficiency vs. SQLite/JSON

### Property-Based Testing (Hypothesis)
- **Fuzz queries** - Random search strings don't crash
- **Round-trip invariants** - Export→Import preserves data
- **Concurrent invariants** - Reads during writes stay consistent

### End-to-End Regression Tests
1. **Fresh install** - `pip install cheese-brain` → create DB → add entity → query
2. **Backup/restore** - Export full DB → delete → import → verify identical
3. **Migration** - Upgrade from v1.0 schema to v2.0 without data loss
4. **Agent integration** - OpenClaw skill can query/update without errors

---

## 🔄 Backup & Recovery

### Backup Strategy
1. **Automatic daily exports** - Cron job exports to `backups/YYYY-MM-DD.json`
2. **Git versioning** - Schema + migrations committed, data `.gitignore`'d
3. **Parquet snapshots** - Compressed columnar format for large datasets
4. **Cloud sync** - Optional: backup to S3/Dropbox/iCloud

### Recovery Procedures

#### Full Database Loss
```bash
# Restore from latest backup
cheese-brain restore backups/2026-02-21.json
# Verify integrity
cheese-brain verify
```

#### Partial Corruption
```bash
# Export good data
cheese-brain export --exclude-corrupt > clean.json
# Rebuild database
rm cheese-brain.duckdb
cheese-brain import clean.json
```

#### Rollback to Previous State
```bash
# Show backup history
cheese-brain backups list
# Restore specific date
cheese-brain restore backups/2026-02-15.json --merge
```

---

## 📅 Project Milestones

### Phase 1: Core Engine (Week 1-2)
- [ ] Repository setup (GitHub, README, LICENSE)
- [ ] DuckDB schema design + migrations
- [ ] Python library: CRUD operations
- [ ] CLI interface (add, list, search, delete)
- [ ] Unit tests (80% coverage)

**Deliverables:**
- `cheese-brain` pip-installable package
- Working CLI for basic operations
- Test suite passing

### Phase 2: Advanced Features (Week 3)
- [ ] Full-text search optimization
- [ ] Import/Export (JSON, CSV, Parquet)
- [ ] Audit log implementation
- [ ] Soft delete + recovery
- [ ] Query DSL (filters, date ranges, tags)

**Deliverables:**
- Backup/restore workflows
- Advanced query capabilities
- Integration tests

### Phase 3: Agent Integration (Week 4)
- [ ] OpenClaw skill wrapper
- [ ] Natural language query interface
- [ ] Automatic entity extraction from conversations
- [ ] Context injection (load relevant entities before agent response)

**Deliverables:**
- `cheese-brain` skill for OpenClaw
- Agent can autonomously query/update knowledge base

### Phase 4: Documentation & Polish (Week 5)
- [ ] Architecture diagrams (Mermaid)
- [ ] API documentation (Sphinx/MkDocs)
- [ ] Usage tutorials (screencast + written)
- [ ] Performance benchmarks report
- [ ] Public launch blog post

**Deliverables:**
- Complete documentation site
- Public GitHub repo
- Launch announcement

---

## 📊 Benchmarks & Tests

### Performance Targets

| Metric | Target | Test Method |
|--------|--------|-------------|
| Insert 1k entities | <1s | Bulk import JSON |
| Query by keyword (10k DB) | <50ms | `SELECT * WHERE title LIKE '%term%'` |
| Full-text search (100k DB) | <200ms | FTS query across all fields |
| Export full DB (10k entities) | <5s | JSON serialization |
| Import from backup | <10s | JSON deserialization + bulk insert |

### Test Coverage Goals
- **Unit tests:** 80% line coverage
- **Integration tests:** All critical paths
- **Regression tests:** 100% of documented use cases

### Benchmark Suite
```bash
# Run all benchmarks
cheese-brain bench

# Example output:
# ✓ Insert 1k entities: 0.42s (2380 ops/s)
# ✓ Query keyword (10k DB): 23ms
# ✓ Full-text search (100k DB): 156ms
# ✓ Export 10k entities: 2.1s
# ✓ Import backup: 4.8s
```

---

## 🛡️ Privacy & Data Scrubbing

### Public Repo Rules
- ❌ No real email addresses, names, phone numbers
- ❌ No API keys, passwords, credentials
- ❌ No proprietary project names/details
- ✅ Synthetic test fixtures only
- ✅ Schema and code are public
- ✅ Anonymized examples in docs

### Data Scrubbing Script
```python
# scrub.py - Remove personal data before git push
def scrub_entity(entity):
    if entity['category'] == 'contact':
        entity['data']['email'] = 'user@example.com'
        entity['data']['name'] = 'John Doe'
    elif entity['category'] == 'api':
        entity['data']['api_key'] = '***REDACTED***'
    return entity
```

---

## 🚀 Deployment Plan

### Local Installation
```bash
pip install cheese-brain
cheese-brain init  # Creates ~/.cheese-brain/cheese-brain.duckdb
cheese-brain add project "SketchySkills" --tags "security,webapp"
cheese-brain search "sketchy"
```

### OpenClaw Integration
```bash
# Install skill
clawhub install cheese-brain-skill
# Agent can now query knowledge base
```

### Continuous Integration
- **GitHub Actions:** Run tests on every push
- **Pre-commit hooks:** Lint + type-check before commit
- **Release automation:** Publish to PyPI on git tag

---

## 📝 Documentation Structure

```
docs/
├── architecture/
│   ├── system-overview.md
│   ├── data-model.md
│   └── diagrams/ (Mermaid source files)
├── user-guide/
│   ├── installation.md
│   ├── quickstart.md
│   ├── cli-reference.md
│   └── api-reference.md
├── developer-guide/
│   ├── contributing.md
│   ├── testing.md
│   └── extending.md
├── operations/
│   ├── backup-recovery.md
│   ├── performance-tuning.md
│   └── troubleshooting.md
└── benchmarks.md
```

---

## 🎯 Success Criteria

This project is **DONE** when:

✅ All 22 entity types can be stored/queried  
✅ <100ms query performance on 10k records  
✅ Full backup/restore works flawlessly  
✅ 100% regression test pass rate  
✅ Documentation complete enough for external users  
✅ OpenClaw skill functional  
✅ Public GitHub repo live with ≥1 external star  

---

## 🧑‍💻 Team & Roles

- **Matt:** Product owner, requirements, acceptance testing
- **Cheese (me):** Architecture, implementation, docs, testing
- **Community:** Future contributors (after public launch)

---

## 📞 Communication

- **Daily updates:** Memory logs (`memory/YYYY-MM-DD.md`)
- **Blockers:** Raise immediately in session
- **Milestone reviews:** End of each phase (demo + retrospective)

---

**Next Step:** Confirm this plan, then I'll start Phase 1 (Core Engine).
