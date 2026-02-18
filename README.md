# 🧀 Cheese Brain

**A DuckDB-powered knowledge management system designed for AI agents and humans who want instant recall.**

[![Tests](https://img.shields.io/github/workflow/status/mhugo22/cheese-brain/tests?label=tests)](https://github.com/mhugo22/cheese-brain/actions)
[![Coverage](https://img.shields.io/codecov/c/github/mhugo22/cheese-brain)](https://codecov.io/gh/mhugo22/cheese-brain)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ClawHub](https://img.shields.io/badge/ClawHub-cheese--brain-orange)](https://clawhub.com/skills/cheese-brain)

---

## Why Cheese Brain?

You've shipped projects, met people, solved problems, and made decisions. But can you recall **why** you chose library X over Y six months ago? Or who that person was you met at the conference?

**Cheese Brain** is your searchable, git-friendly second brain built on DuckDB. It's:

- 🚀 **Fast** - Sub-1ms keyword queries, 5ms FTS with BM25 ranking
- 🧠 **Flexible** - 22+ entity types (projects, contacts, APIs, decisions, and more)
- 🔍 **Full-Text Search** - Relevance-ranked results with stemming & stopword filtering
- 🤖 **Agent-ready** - Designed for AI assistants to query/update autonomously
- 📦 **Portable** - Single-file database, no server required
- 🔒 **Private** - Your data stays local (optional cloud backup)

---

## Quick Start

### Python/CLI Installation

```bash
# Clone and install
git clone https://github.com/mhugo22/cheese-brain.git
cd cheese-brain
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .

# Verify installation
cheese-brain stats
```

### OpenClaw Skill Installation

For OpenClaw users (AI agent framework):

```bash
# Install the skill from ClawHub
clawhub install cheese-brain

# Your AI agent can now query Cheese Brain autonomously
```

**Skill page:** https://clawhub.com/skills/cheese-brain

### Basic Usage

```bash
# Add your first entity
cheese-brain add \
  --title "SketchySkills" \
  --category project \
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

### "What was the email monitor project?"
```bash
$ cheese-brain search "email monitor"
```
Returns: **Email Monitor** project with full context (repo, path, schedule, run command)

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

### "What's the calendar feed for group X?"
```bash
$ cheese-brain search "calendar feed"
```
Returns: Contact entity with ICS calendar feed URL, location, timezone

**The problem this solves:** Instead of asking "What's that project?" or grepping through files, you get instant, structured answers with all the context you need.

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

# Full-text search (BM25 relevance ranking)
cheese-brain fts "backup config"
# Returns: Config Backup Script (score: 2.413) - best match first

# Filter by category
cheese-brain list --category contact

# Date range
cheese-brain list --since 2026-01-01

# Tags
cheese-brain list --tags security,webapp
```

**FTS vs Regular Search:**
- **FTS:** Relevance-ranked (BM25), stemming, stopword filtering
- **Regular:** Chronological, exact matches, category/tag/date filters
- [Full FTS documentation →](FTS.md)

### 🔗 Relationship Tracking

Link entities together to build a knowledge graph:

```bash
# Create relationships
cheese-brain link <workflow-id> <tool-id> --type uses
cheese-brain link <email-id> <project-id> --type belongs_to

# View relationships
cheese-brain links <entity-id>
# Output:
# 📎 Relationships for: Gabby Gmail Monitor
#   → uses → Gmail API Integration (infrastructure)
#   → related_to → Gabby Gmail Repository (bookmark)

# Visual graph
cheese-brain graph <entity-id>
# Output:
# 🔗 Relationship Graph
# USES
#   → Gmail API Integration (infrastructure)
# RELATED_TO
#   → Gabby Gmail Repository (bookmark)

# Delete relationship
cheese-brain unlink <relationship-id>
```

**Relationship Types:**
- `uses` - Workflow uses Tool, Project uses Email
- `belongs_to` - Email belongs to Project
- `requires` - Project requires Infrastructure
- `related_to` - Generic bidirectional link
- `depends_on` - Project depends on Service
- `documents` - Bookmark documents Project
- `implements` - Code implements Design

**Use cases:**
- "What tools does this workflow use?"
- "Which projects use this email account?"
- "Show me all documentation for this project"
- Build dependency graphs for projects

### 🔄 Backup & Restore

```bash
# Export to JSON (human-readable)
cheese-brain export backup.json

# Export to Parquet (2-9x smaller)
cheese-brain export backup.parquet --format parquet

# Restore from backup (auto-detects format)
cheese-brain restore-backup backup.json
cheese-brain restore-backup backup.parquet

# Automated daily backups
# See BACKUP_RECOVERY.md for full setup guide
```

**Parquet vs JSON:**
- Parquet: 2-9x smaller (scales with data size), binary format
- JSON: Human-readable, easier debugging
- Both: Same fidelity, lossless roundtrip

### 🤖 AI Agent Integration

Built for OpenClaw and other agent frameworks:

```python
from cheese_brain import CheeseBrain

brain = CheeseBrain()

# Agent queries knowledge base
results = brain.search("email monitor")
# Returns: [{'category': 'project', 'title': 'Email Monitor', ...}]

# Agent adds new knowledge
brain.add_entity(
    category="decision",
    title="Why we chose DuckDB",
    data={"reason": "Fast analytics, git-friendly, zero config"},
    tags=["architecture", "database"]
)

# Agent builds knowledge graph
from cheese_brain.models import RelationshipType

brain.add_relationship(
    from_id=workflow_id,
    to_id=tool_id,
    relationship_type=RelationshipType.USES
)

# Agent queries relationships
relationships = brain.get_relationships(entity_id)
# Returns: [(relationship, related_entity), ...]
```

---

## 🔒 Security

Cheese Brain includes multiple security layers:

### 🗂️ File Permissions
Database and backups automatically secured with owner-only permissions (`0600`)

### 🏷️ Sensitive Field Redaction
Auto-redacts `password`, `api_key`, `token`, `secret` fields in output
```bash
cheese-brain get <id>         # Redacted by default
cheese-brain get <id> --reveal  # Show real values
```

### 🔐 Encrypted Backups
Password-protect export files
```bash
cheese-brain export backup.json --encrypt
cheese-brain restore-backup backup.json  # Auto-detects encryption
```

### 🛡️ Data Validation
- Max 1MB per entity
- Max 10 levels of nesting
- SQL injection protection (parameterized queries)

**[Full Security Documentation →](SECURITY.md)**

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
│ Entities | Relationships | Audit Log       │
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
