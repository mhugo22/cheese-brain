# Changelog

All notable changes to Cheese Brain will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Critical bug:** Fixed foreign key constraint error when updating entities with relationships. DuckDB's foreign key implementation was blocking updates even when the ID field wasn't being modified. The `update()` method now temporarily removes relationships, performs the update, then restores them within a transaction. This is a workaround for DuckDB's lack of CASCADE support on foreign keys. ([#1](https://github.com/mhugo22/cheese-brain/issues/1))

### Added
- Test coverage for updating entities with relationships (`test_update_entity_with_relationships`)

### Changed
- Coverage improved from 39% to 41%

## [1.0.0] - 2026-02-18

### Added
- **Phase 2 Complete:** All 5 sprints shipped
  - Sprint 1: Relationship tracking (knowledge graph with 7 relationship types)
  - Sprint 2: Bulk import (CSV/JSON with duplicate handling)
  - Sprint 3: Advanced queries (multi-field filtering, tag logic, JSON paths, date ranges)
  - Sprint 4: OpenClaw integration (unified search with memory files)
  - Sprint 5: Auto-capture (extract entities from markdown notes)
- Advanced query method with tag modes (all/any), date ranges, JSON filtering, sorting
- Relationship commands: `link`, `unlink`, `links`, `graph`
- Bulk import commands: `import-bulk` with dry-run and merge support
- Auto-capture command: `scan` with confidence scoring and auto-add
- 17 tests total (all passing), 39% coverage initially
- Comprehensive documentation: PHASE2_COMPLETE.md, RELATIONSHIPS.md, CHEESE_BRAIN_WORKFLOWS.md
- Integration into agent workflow (SOUL.md, MEMORY.md, AGENTS.md)

### Security
- All personal paths sanitized (`/Users/sloth` → `~`)
- Example API keys sanitized in documentation
- Security scan passed (0 sensitive data in public repo)

## [0.1.0] - 2026-02-17

### Added
- **Phase 1 Complete:** Core knowledge base engine
- DuckDB-based storage with sub-millisecond queries
- 22+ entity categories (project, tool, workflow, contact, decision, etc.)
- CLI with commands: add, get, search, list, update, delete, stats, tags
- Full-text search (FTS) with BM25 relevance ranking
- Parquet export/import (2-9x compression)
- Automated daily backups (JSON format, 30-day retention)
- Security features: file permissions (0600), sensitive field redaction, encrypted exports, JSON validation
- Comprehensive documentation: README, WHITEPAPER, SECURITY.md, FTS.md, BACKUP_RECOVERY.md
- Published to ClawHub as OpenClaw skill
- 13 tests (all passing), 61% coverage initially

[Unreleased]: https://github.com/mhugo22/cheese-brain/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mhugo22/cheese-brain/releases/tag/v1.0.0
[0.1.0]: https://github.com/mhugo22/cheese-brain/releases/tag/v0.1.0
