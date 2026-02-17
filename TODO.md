# Cheese Brain - TODO & Improvements

**Last Updated:** 2026-02-17  
**Phase 1 Status:** ✅ COMPLETE  
**Current entities:** 9 of 39 cataloged

---

## 📦 Remaining Entities to Add (30)

### Projects (2)
- [ ] 2024 Honda Talon - active project with parts/weight tracking
- [ ] Built with Cheese Portfolio - portfolio repo

### Tools & Infrastructure (7)
- [ ] Config Backup Script (`backup_config.py`)
- [ ] Config Restore Script (`restore_config.py`)
- [ ] News Monitoring System (`/workspace/news/`)
- [ ] Calendar Integration Scripts (`/workspace/calendar/`)
- [ ] Cost Monitor Script (`cost-monitor.js`)
- [ ] Rate Limit Probe Script (`probe-rate-limit.js`)
- [ ] Validation Scripts (deployment, accessibility)

### Workflows (3)
- [ ] Track-Before-Do Rule - non-trivial work policy
- [ ] Config Change Workflow - backup → confirm → apply → restart
- [ ] Daily Digest Workflow - board → daily note → clear Done

### Data Sources (3)
- [ ] Daily Notes (`10 Daily/YYYY-MM-DD.md`)
- [ ] Matt Kanban Board (`10 Daily/Matt - Task Board`)
- [ ] MEMORY.md - long-term curated memory

### Documentation (5)
- [ ] Cheese Technical Documentation
- [ ] OpenClaw Config Recovery Guide
- [ ] How We Use This Brain (Obsidian guidelines)
- [ ] Project Templates (PROJECT_TEMPLATE, RETROSPECTIVE_TEMPLATE)
- [ ] Security rollup templates

### Repositories (4)
- [ ] OpenClaw Workspace Repo
- [ ] SketchySkills Repo (already added as project, could add as separate repo entity)
- [ ] Gabby Gmail Repo (same as above)
- [ ] Cheese Brain Repo (this repo)

### Policies (3)
- [ ] Security Logging Policy (40 Reference/Security/)
- [ ] No Outbound Communication Policy
- [ ] Calendar Write Confirmation Policy

### Areas of Focus (3)
- [ ] Weight Loss Tracking (30 Areas/Weight loss/)
- [ ] Bowling Tracking (30 Areas/Bowling/)
- [ ] Cooking/Recipes (30 Areas/Cooking/)
- [ ] Music - 1001 Albums tracker

### Integrations (3)
- [ ] Telegram Integration (channel config, bot token)
- [ ] Gmail API (Gabby OAuth config)
- [ ] Apple Calendar (iCloud integration)

---

## 🚀 Phase 2 Features (From PROJECT_PLAN.md)

### Advanced Search & Retrieval
- [ ] Full-text search (FTS) implementation
  - Enable FTS index: `PRAGMA create_fts_index('entities', 'id', 'title', 'data')`
  - Add FTS search to CLI: `cheese-brain fts "full text query"`
  - Benchmark FTS vs keyword search performance
- [ ] Cross-reference detection
  - Find entities that reference each other
  - Build relationship graph
- [ ] Semantic search (optional, requires embeddings)
  - Generate embeddings for entity titles + descriptions
  - Vector similarity search for "things like X"

### Backup & Export
- [x] **Automated daily JSON exports** ✅
  - Cron job: runs daily at 2:00 AM CST
  - Location: `~/.cheese-brain/backups/YYYY-MM-DD.json`
  - Retention: 30 days (automatic cleanup)
  - Script: `/Users/sloth/.openclaw/workspace/scripts/backup_cheese_brain.sh`
  - Log: `~/.cheese-brain/backup.log`
  - First backup: 44 entities, 32KB
  - Documentation: `BACKUP_RECOVERY.md` (12KB with full recovery procedures)
- [ ] Parquet export support (9x compression)
  - Add `cheese-brain export --format parquet` command
  - Benchmark file sizes vs JSON
- [ ] ~~Git-friendly exports to workspace~~ (NOT SAFE - repo is public, sensitive data in DB)
  - Alternative: Manual weekly copy to private location (Time Machine, external drive)

### CLI Enhancements
- [ ] Bulk import from JSON/CSV
  - `cheese-brain import entities.json`
  - Support CSV format for spreadsheet users
- [ ] Interactive mode
  - `cheese-brain shell` - REPL interface
  - Tab completion for commands/categories/tags
- [ ] Query builder
  - `cheese-brain query --category project --tag shipped --created-after 2026-01-01`
  - Advanced filtering combinations
- [ ] Fuzzy search
  - Typo tolerance in search queries
  - "Did you mean...?" suggestions

### Data Quality
- [ ] Duplicate detection
  - Find entities with similar titles
  - Suggest merges
- [ ] Orphaned tag cleanup
  - List tags used only once
  - Suggest consolidation (e.g., "automation" vs "automated")
- [ ] Data validation
  - Required fields per category
  - JSON schema validation for data field
  - URL validation for repo/live links

---

## 🔗 Integration Opportunities

### OpenClaw Memory System
- [ ] Bridge to `memory_search` tool
  - Add Cheese Brain results to memory search
  - Unified search across MEMORY.md + daily notes + Cheese Brain
- [ ] Heartbeat integration
  - Check for entities modified today
  - Report stats during heartbeat
- [ ] Auto-capture from daily notes
  - Parse 🧀 Cheese Digest sections
  - Extract project names, tool mentions → auto-add to Cheese Brain

### Obsidian Integration
- [ ] Obsidian plugin (future)
  - Search Cheese Brain from Obsidian command palette
  - Insert entity links as Obsidian notes
  - Sync tags between Obsidian + Cheese Brain
- [ ] Dataview queries
  - Export entities as Obsidian notes
  - Query from Dataview plugin
- [ ] Daily note templates
  - Auto-generate daily note sections from Cheese Brain entities
  - "Today's projects" section with active entities

### CLI Skill for OpenClaw
- [ ] Create `cheese-brain` skill in `/skills/cheese-brain/`
  - SKILL.md with usage examples
  - Wrapper scripts for common operations
  - Make it easy for other OpenClaw users to adopt

---

## 📈 Performance Optimization

### Indexing
- [ ] Benchmark index performance
  - Test with 10k, 100k, 1M entities
  - Measure index overhead vs query speed
- [ ] Expression index on JSON fields
  - Frequently queried JSON keys (status, repo, path)
  - `CREATE INDEX idx_status ON entities((json_extract_string(data, '$.status')))`
- [ ] Composite indexes
  - Common query patterns: category + tags, category + created_at

### Query Optimization
- [ ] Prepared statements
  - Cache frequently-used queries
  - Reduce parsing overhead
- [ ] Connection pooling (if needed)
  - May not be necessary for single-user embedded DB
  - Monitor for bottlenecks first

### Storage
- [ ] Database size monitoring
  - Track growth over time
  - Alert when approaching size limits
- [ ] Vacuum/optimization
  - Periodic VACUUM to reclaim space
  - ANALYZE to update query planner stats

---

## 🧪 Testing & Quality

### Test Coverage
- [ ] Increase coverage to 80%+
  - CLI tests (currently 34% coverage)
  - Error handling paths
  - Edge cases (empty DB, malformed JSON, etc.)
- [ ] Integration tests
  - End-to-end CLI workflows
  - Export → import roundtrip
  - Concurrent access (if needed)
- [ ] Performance regression tests
  - Benchmark suite
  - CI/CD checks for query performance

### Documentation
- [ ] Usage examples in README
  - Common workflows
  - Screenshots/GIFs of CLI
- [ ] API documentation
  - Docstrings for all public methods
  - Sphinx or pdoc3 generated docs
- [ ] Video walkthrough
  - YouTube demo
  - Link from README

---

## 🎨 UX Improvements

### CLI Output
- [ ] Colorization
  - Color-coded categories
  - Highlighted search terms
  - Error messages in red
- [ ] Pagination
  - `cheese-brain list --limit 20 --page 2`
  - Handle large result sets gracefully
- [ ] Output formats
  - `--format json` for scripting
  - `--format table` (default)
  - `--format csv` for exports

### Aliases & Shortcuts
- [ ] Short aliases
  - `cb` as alias for `cheese-brain`
  - `cb s` for search
  - `cb a` for add
- [ ] Smart defaults
  - `cb search` without args → interactive prompt
  - `cb add` → interactive form with prompts

---

## 🔐 Security & Privacy

### Data Protection
- [ ] Encryption at rest (optional)
  - SQLCipher for encrypted DuckDB
  - Protect sensitive entity data
- [ ] Sensitive field redaction
  - Mark fields as sensitive (tokens, passwords)
  - Redact in list/search output
  - Show only in `get` with confirmation

### Audit Logging
- [ ] Enhanced audit log
  - Track who/when/what changed (useful for multi-user setups)
  - Audit log search/export
- [ ] Retention policy
  - Auto-delete audit logs older than X days
  - Configurable retention

---

## 🌐 Future Enhancements (Ambitious)

### Multi-User Support
- [ ] User accounts
  - Multiple users, each with isolated entities
  - Shared entities (team knowledge bases)
- [ ] Permissions
  - Read/write/admin roles
  - Entity-level access control

### Web UI
- [ ] Flask/FastAPI web interface
  - Browse entities in browser
  - Rich text editor for data field
  - Visual tag cloud
- [ ] REST API
  - HTTP endpoints for CRUD operations
  - API keys for authentication
  - OpenAPI/Swagger docs

### AI Integration
- [ ] Natural language queries
  - "Show me all shipped projects from January"
  - "What tools do I have for backups?"
- [ ] Auto-tagging
  - LLM suggests tags based on entity content
  - Auto-categorization
- [ ] Entity summarization
  - LLM generates summaries for long data fields
  - Extract key points

### Sync & Cloud
- [ ] Cloud backup
  - S3/GCS/Dropbox integration
  - Encrypted cloud backups
- [ ] Multi-device sync
  - Sync across multiple machines
  - Conflict resolution

---

## 🐛 Known Issues

- [ ] Duplicate "Gabby Gmail Monitor" entries
  - Currently 2 entries (from different sessions)
  - Need deduplication script or manual cleanup
- [ ] No validation for duplicate titles
  - Should warn/prevent adding duplicate entity names
- [ ] CLI doesn't validate JSON data format
  - Malformed JSON crashes add/update commands
  - Need try/catch + user-friendly error messages

---

## 📅 Priority Recommendations

### High Priority (Do Soon)
1. **Add remaining 30 entities** - complete the initial knowledge base
2. **Automated backups** - JSON export cron job (daily)
3. **Fix duplicate Gabby Gmail** - clean up test data
4. **Usage examples in README** - help others understand how to use it

### Medium Priority (Phase 2)
1. **Full-text search (FTS)** - for larger datasets
2. **Bulk import** - easier to populate from spreadsheets
3. **OpenClaw skill** - package as reusable skill
4. **Increase test coverage** - 80%+ for reliability

### Low Priority (Nice to Have)
1. **Web UI** - visual interface for browsing
2. **Natural language queries** - AI-powered search
3. **Multi-user support** - if other people adopt this

### Backlog (Future Ideas)
1. **Obsidian plugin** - deep integration with Obsidian
2. **Cloud sync** - sync across devices
3. **Encryption** - for sensitive data

---

## 🎯 Next Session Goals

**Immediate tasks:**
1. Add remaining 30 entities (batch import script?)
2. Set up daily backup cron
3. Clean up duplicate Gabby Gmail entry
4. Update README with usage examples

**Or:**
- Start Phase 2 features (FTS, advanced search)
- Build OpenClaw skill wrapper
- Focus on other projects (let Cheese Brain simmer)

---

**Questions for Matt:**
- Priority: finish populating entities vs. Phase 2 features?
- Keep as personal tool or package for other OpenClaw users?
- Any specific integrations you want first (Obsidian, memory_search)?
