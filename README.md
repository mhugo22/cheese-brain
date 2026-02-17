# 🧀 Cheese Brain

**A DuckDB-powered knowledge management system designed for AI agents and humans who want instant recall.**

[![Tests](https://img.shields.io/github/workflow/status/mhugo22/cheese-brain/tests?label=tests)](https://github.com/mhugo22/cheese-brain/actions)
[![Coverage](https://img.shields.io/codecov/c/github/mhugo22/cheese-brain)](https://codecov.io/gh/mhugo22/cheese-brain)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Why Cheese Brain?

You've shipped projects, met people, solved problems, and made decisions. But can you recall **why** you chose library X over Y six months ago? Or who that person was you met at the conference?

**Cheese Brain** is your searchable, git-friendly second brain built on DuckDB. It's:

- 🚀 **Fast** - Sub-100ms keyword queries on 10k+ records
- 🧠 **Flexible** - 22+ entity types (projects, contacts, APIs, decisions, and more)
- 🤖 **Agent-ready** - Designed for AI assistants to query/update autonomously
- 📦 **Portable** - Single-file database, no server required
- 🔒 **Private** - Your data stays local (optional cloud backup)

---

## Quick Start

```bash
# Install
pip install cheese-brain

# Initialize database
cheese-brain init

# Add your first entity
cheese-brain add project "SketchySkills" \
  --tags "security,webapp" \
  --data '{"url": "https://sketchyskills.vercel.app", "status": "shipped"}'

# Search
cheese-brain search "sketchy"
# Output:
# 🧀 [project] SketchySkills
# Tags: security, webapp
# Status: shipped
# URL: https://sketchyskills.vercel.app

# Backup
cheese-brain export backups/2026-02-21.json
```

---

## Real-World Examples

From a working knowledge base with 44 entities:

### "What was gabby email?"
```bash
$ cheese-brain search "gabby email"
```
Returns: **Gabby Gmail Monitor** project with full context (repo, path, schedule, run command)

### "How do I backup config?"
```bash
$ cheese-brain search "backup config"
```
Returns: **Config Backup Script** + **Config Change Workflow** + **Recovery Guide**

### "Show me all shipped projects"
```bash
$ cheese-brain list --category project --tags shipped
```
Returns: SketchySkills, Gabby Gmail Monitor

### "What's the scouts calendar feed?"
```bash
$ cheese-brain search "scout calendar"
```
Returns: **Scouts Troop 725G** contact with Band.us ICS feed URL, location, timezone

**The problem this solves:** Instead of asking "What's gabby email?" or grepping through files, you get instant, structured answers with all the context you need.

---

## Features

### 📚 Supported Entity Types

Track anything that matters:

- Projects, Tools, APIs, Contacts, Decisions
- Code snippets, Workflows, Troubleshooting solutions
- Meeting notes, Ideas, Failed experiments
- And 11 more ([full list](docs/entity-types.md))

### 🔍 Powerful Queries

```bash
# Keyword search
cheese-brain search "email"

# Filter by category
cheese-brain list --category contact

# Date range
cheese-brain list --since 2026-01-01

# Tags
cheese-brain list --tags security,webapp
```

### 🔄 Backup & Restore

```bash
# Export to JSON
cheese-brain export backup.json

# Restore from backup
cheese-brain restore backup.json

# Automated daily backups (cron)
0 2 * * * cheese-brain export ~/backups/$(date +\%Y-\%m-\%d).json
```

### 🤖 AI Agent Integration

Built for OpenClaw and other agent frameworks:

```python
from cheese_brain import CheeseBrain

brain = CheeseBrain()

# Agent queries knowledge base
results = brain.search("email gabby")
# Returns: [{'category': 'email', 'title': 'gabby@example.com', ...}]

# Agent adds new knowledge
brain.add_entity(
    category="decision",
    title="Why we chose DuckDB",
    data={"reason": "Fast analytics, git-friendly, zero config"},
    tags=["architecture", "database"]
)
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│      CLI / Python API / OpenClaw Skill      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Cheese Brain Core Library           │
│  Query Engine | CRUD | Import/Export        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            DuckDB Engine                    │
│  Entities (JSON + Arrays) | Audit Log       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│   cheese-brain.duckdb (local file)         │
└─────────────────────────────────────────────┘
```

[Full architecture docs →](docs/architecture/system-overview.md)

---

## Performance

Real benchmarks from prototype testing (M2 Mac mini, 10k entities):

| Operation | Records | Avg Time |
|-----------|---------|----------|
| Keyword search | 10,000 | 0.47ms |
| Tag search | 10,000 | 0.54ms |
| Category filter | 10,000 | 0.82ms |
| JSON field filter | 10,000 | 5.10ms |
| FTS BM25 search | 10,000 | 5.22ms |
| Batch insert | 10,000 | 53k ops/sec |

**Export compression:** Parquet format = 9x smaller than JSON (343KB vs 3,092KB)

[Full benchmark methodology →](WHITEPAPER.md#appendix-b-benchmarks)

---

## Documentation

- [Installation Guide](docs/user-guide/installation.md)
- [Quick Start Tutorial](docs/user-guide/quickstart.md)
- [CLI Reference](docs/user-guide/cli-reference.md)
- [Python API](docs/user-guide/api-reference.md)
- [Architecture](docs/architecture/system-overview.md)
- [Backup & Recovery](docs/operations/backup-recovery.md)
- [Contributing](docs/developer-guide/contributing.md)

---

## Why DuckDB?

- **Columnar storage** - Efficient for analytical queries
- **JSON support** - Flexible schema without sacrificing speed
- **Single-file** - No server, no config, just works
- **Git-friendly** - Export to JSON/Parquet for version control
- **Fast** - 10-100x faster than SQLite for complex queries

---

## Development Status

✅ **Phase 1 Complete** - Production-ready core engine + CLI

**Stats:**
- 44 entities across 8 categories
- 13/13 tests passing (61% coverage)
- Sub-millisecond search performance
- Database size: 28 MB

**Next Phase:** Advanced features (FTS, batch import, automated backups)

[View project plan →](PROJECT_PLAN.md) | [View TODO →](TODO.md)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/developer-guide/contributing.md) for:

- Code style guide
- Testing requirements
- PR process

---

## License

MIT License - see [LICENSE](LICENSE) for details

---

## Acknowledgments

- Built with [DuckDB](https://duckdb.org/)
- Inspired by the "Second Brain" methodology (Tiago Forte)
- Designed for [OpenClaw](https://openclaw.ai/) agent framework

---

**Built with 🧀 by Cheese (AI assistant) for Matt H.**

*Track knowledge. Recall instantly. Never forget why.*
