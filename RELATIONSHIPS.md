# 🔗 Cheese Brain Relationships

**Build a knowledge graph by linking entities together.**

Version: 1.1.0 | Last Updated: 2026-02-18

---

## Why Relationships?

Your knowledge isn't isolated facts — it's a connected web. Relationships let you answer questions like:

- "What tools does this workflow use?"
- "Which projects depend on this API?"
- "Show me all documentation for this project"
- "What email accounts belong to this client?"

Instead of remembering connections manually, Cheese Brain tracks them for you.

---

## Quick Start

```bash
# Create a relationship
cheese-brain link <from-id> <to-id> --type uses

# View relationships for an entity
cheese-brain links <entity-id>

# Visualize the graph
cheese-brain graph <entity-id>

# Delete a relationship
cheese-brain unlink <relationship-id>
```

---

## Relationship Types

Cheese Brain supports 7 semantic relationship types:

| Type | Direction | Meaning | Example |
|------|-----------|---------|---------|
| `uses` | directional | A uses B | Workflow uses Tool |
| `belongs_to` | directional | A belongs to B | Email belongs to Project |
| `requires` | directional | A requires B | Project requires API |
| `depends_on` | directional | A depends on B | App depends on Infrastructure |
| `documents` | directional | A documents B | Bookmark documents Project |
| `implements` | directional | A implements B | Code implements Design |
| `related_to` | bidirectional | A and B are related | Project related to Meeting |

**Directional vs Bidirectional:**
- **Directional:** A → B has a specific meaning (`uses`, `requires`, etc.)
- **Bidirectional:** A ↔ B are simply connected (`related_to`)

---

## CLI Usage

### Create Relationships

```bash
# Basic link
cheese-brain link <from-id> <to-id> --type uses

# With metadata note
cheese-brain link <workflow-id> <api-id> \
  --type requires \
  --note "OAuth 2.0 required for authentication"

# Example: Link workflow to tools
cheese-brain link a6a16457-180f-44ef-9b90-bd32ec24f351 \
                  83ce8ac8-63ec-4a3d-9e73-0e74702bac89 \
                  --type uses \
                  --note "Gmail API for email monitoring"
```

**Output:**
```
✅ Created relationship: c89edae8-8944-45e8-a07b-8ad0965e71df
   From: a6a16457-180f-44ef-9b90-bd32ec24f351
   To: 83ce8ac8-63ec-4a3d-9e73-0e74702bac89
   Type: uses
   Note: Gmail API for email monitoring
```

### View Relationships

```bash
# Show all relationships for an entity
cheese-brain links <entity-id>

# Filter by direction
cheese-brain links <entity-id> --direction from  # Only outgoing
cheese-brain links <entity-id> --direction to    # Only incoming

# Filter by type
cheese-brain links <entity-id> --type uses

# JSON output
cheese-brain links <entity-id> --format json
```

**Example Output (Table):**
```
📎 Relationships for: Gabby Gmail Monitor
   Category: workflow
   ID: a6a16457-180f-44ef-9b90-bd32ec24f351

                          Relationships (2 total)                          
┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Direction ┃ Type       ┃ Related Entity        ┃ Category       ┃ Rel ID      ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ →         │ uses       │ Gmail API Integration │ infrastructure │ c89edae8... │
│ →         │ related_to │ Gabby Gmail Repository│ bookmark       │ e0807a32... │
└───────────┴────────────┴───────────────────────┴────────────────┴─────────────┘
```

**Direction Arrows:**
- `→` = Outgoing (this entity is the source)
- `←` = Incoming (this entity is the target)

### Visual Graph

```bash
# Show relationship graph
cheese-brain graph <entity-id>

# With filters
cheese-brain graph <entity-id> --type uses
cheese-brain graph <entity-id> --depth 2  # Future: multi-level traversal
```

**Example Output:**
```
🔗 Relationship Graph

📍 Root: Gabby Gmail Monitor
   Category: workflow
   ID: a6a16457-180f-44ef-9b90-bd32ec24f351

USES
  → Gmail API Integration (infrastructure)

RELATED_TO
  → Gabby Gmail Repository (bookmark)

Total relationships: 2
```

### Delete Relationships

```bash
# Delete by relationship ID
cheese-brain unlink <relationship-id>

# Example
cheese-brain unlink c89edae8-8944-45e8-a07b-8ad0965e71df
```

---

## Python API

### Basic Operations

```python
from cheese_brain import CheeseBrain
from cheese_brain.models import RelationshipType
from uuid import UUID

brain = CheeseBrain()

# Create relationship
rel_id = brain.add_relationship(
    from_id=UUID('a6a16457-180f-44ef-9b90-bd32ec24f351'),
    to_id=UUID('83ce8ac8-63ec-4a3d-9e73-0e74702bac89'),
    relationship_type=RelationshipType.USES,
    metadata={"note": "Gmail API for monitoring"}
)

# Get relationships
relationships = brain.get_relationships(
    entity_id=UUID('a6a16457-180f-44ef-9b90-bd32ec24f351'),
    direction="both",  # "from", "to", or "both"
    relationship_type=RelationshipType.USES  # Optional filter
)

for rel, related_entity in relationships:
    print(f"{rel.relationship_type.value}: {related_entity.title}")

# Get relationship graph
graph = brain.get_relationship_graph(
    entity_id=UUID('a6a16457-180f-44ef-9b90-bd32ec24f351'),
    depth=1  # Current depth=1 only; multi-level coming in Phase 2
)

print(f"Root: {graph['entity'].title}")
for rel_data in graph['relationships']:
    print(f"  {rel_data['type']}: {rel_data['related'].title}")

# Delete relationship
brain.delete_relationship(rel_id)
```

### Return Types

**`get_relationships()` returns:**
```python
[
    (Relationship, Entity),  # Tuple of relationship + related entity
    ...
]
```

**Relationship object:**
```python
Relationship(
    id=UUID('c89edae8-8944-45e8-a07b-8ad0965e71df'),
    from_id=UUID('a6a16457-180f-44ef-9b90-bd32ec24f351'),
    to_id=UUID('83ce8ac8-63ec-4a3d-9e73-0e74702bac89'),
    relationship_type=RelationshipType.USES,
    metadata={"note": "Gmail API for monitoring"},
    created_at=datetime(...)
)
```

**`get_relationship_graph()` returns:**
```python
{
    "entity": Entity(...),  # Root entity
    "relationships": [
        {
            "type": "uses",
            "direction": "from",  # or "to"
            "related": Entity(...),
            "depth": 1,
            "relationship_id": "c89edae8-..."
        },
        ...
    ]
}
```

---

## Common Patterns

### 1. Document All Tools for a Workflow

```bash
# Find workflow
cheese-brain search "Gabby Gmail Monitor"
# → workflow ID: a6a16457-180f-44ef-9b90-bd32ec24f351

# Find tools
cheese-brain search "Gmail API"
# → infrastructure ID: 83ce8ac8-63ec-4a3d-9e73-0e74702bac89

cheese-brain search "Python email"
# → tool ID: 9bf9bd3a-...

# Link them
cheese-brain link a6a16457-... 83ce8ac8-... --type uses
cheese-brain link a6a16457-... 9bf9bd3a-... --type uses

# View all tools
cheese-brain links a6a16457-... --type uses
```

### 2. Track Project Dependencies

```python
# Add project + infrastructure
project_id = brain.add_entity(
    category="project",
    title="Web Dashboard",
    data={"url": "https://dashboard.example.com"}
)

db_id = brain.add_entity(
    category="infrastructure",
    title="PostgreSQL Database",
    data={"host": "db.example.com"}
)

api_id = brain.add_entity(
    category="api",
    title="Stripe API",
    data={"version": "2024-11-20"}
)

# Link dependencies
brain.add_relationship(project_id, db_id, RelationshipType.REQUIRES)
brain.add_relationship(project_id, api_id, RelationshipType.DEPENDS_ON)

# Query dependencies
deps = brain.get_relationships(project_id, direction="from")
print(f"Project depends on: {[e.title for _, e in deps]}")
```

### 3. Bidirectional "Related To"

```python
# Create bidirectional link
brain.add_relationship(
    meeting_note_id,
    decision_id,
    RelationshipType.RELATED_TO,
    metadata={"context": "This decision was made during the meeting"}
)

# Query from either direction
brain.get_relationships(meeting_note_id)  # Shows decision
brain.get_relationships(decision_id)      # Shows meeting note
```

---

## Database Schema

```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY,
    from_id UUID NOT NULL,
    to_id UUID NOT NULL,
    relationship_type VARCHAR NOT NULL CHECK (relationship_type IN (
        'uses', 'belongs_to', 'requires', 'related_to',
        'depends_on', 'documents', 'implements'
    )),
    metadata JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_id) REFERENCES entities(id),
    FOREIGN KEY (to_id) REFERENCES entities(id)
);

-- Indexes for fast lookups
CREATE INDEX idx_rel_from ON relationships(from_id);
CREATE INDEX idx_rel_to ON relationships(to_id);
CREATE INDEX idx_rel_type ON relationships(relationship_type);
```

**Notes:**
- Foreign keys ensure referential integrity
- DuckDB doesn't support CASCADE deletes, so orphaned relationships stay in the DB
- Deleted entities are hidden via `deleted_at IS NULL` filter

---

## Migration from 1.0.0 to 1.1.0

**Automatic migration:** When you first run Cheese Brain 1.1.0, it automatically:
1. Detects schema version 1.0.0
2. Creates `relationships` table
3. Updates schema version to 1.1.0
4. No data loss, fully backward compatible

**Manual check:**
```python
from cheese_brain import CheeseBrain

brain = CheeseBrain()
version = brain.conn.execute(
    "SELECT json_extract_string(value, '$.version') FROM metadata WHERE key = 'schema_version'"
).fetchone()

print(f"Schema version: {version[0]}")  # Should be "1.1.0"
```

---

## Future Enhancements (Phase 2+)

- **Multi-level graph traversal** - `depth=2` to show relationships of relationships
- **Relationship search** - Find all entities with relationship type X
- **Inverse relationships** - Auto-create reverse links (e.g., `uses` ↔ `used_by`)
- **Relationship counts** - Show # of dependencies per entity
- **Graph visualization** - Export to GraphViz/Mermaid
- **Bulk relationship import** - CSV format for mass linking

---

## Troubleshooting

### "Entity not found" error
```bash
# Error: Source entity abc123 not found
```

**Solution:** Verify entity IDs exist:
```bash
cheese-brain get abc123
cheese-brain search "entity name"
```

### No relationships showing
```bash
# cheese-brain links <id> shows no results
```

**Checklist:**
1. Verify relationships exist: `cheese-brain links <id> --format json`
2. Check direction filter: Try `--direction both`
3. Check type filter: Remove `--type` to see all types
4. Verify entity isn't deleted: `cheese-brain get <id>`

### Relationship to deleted entity
Relationships to deleted entities are automatically hidden in query results. The relationship still exists in the database but won't appear in `links` or `graph` output.

---

## See Also

- [Main README](README.md) - Installation and basic usage
- [FTS.md](FTS.md) - Full-text search documentation
- [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) - Backup and recovery guide
- [SECURITY.md](SECURITY.md) - Security features

---

**Questions? Feedback?**
- GitHub Issues: https://github.com/mhugo22/cheese-brain/issues
- ClawHub: https://clawhub.com/skills/cheese-brain
