# Full-Text Search (FTS) - User Guide

**Last Updated:** 2026-02-17

Cheese Brain includes Full-Text Search powered by DuckDB's FTS extension with BM25 relevance ranking.

---

## What is FTS?

**FTS (Full-Text Search)** is a specialized search technique that:
- **Ranks results by relevance** using BM25 scoring algorithm
- **Searches across multiple fields** (title, category)
- **Handles stemming** (e.g., "backup" matches "backed", "backing")
- **Ignores stopwords** (common words like "the", "a", "is")
- **Returns best matches first** (not chronological order)

---

## FTS vs Regular Search

| Feature | Regular Search | FTS Search |
|---------|----------------|------------|
| **Speed** | Fast (< 1ms) | Fast (< 5ms) |
| **Ranking** | No (chronological) | Yes (BM25 relevance) |
| **Stemming** | No | Yes |
| **Multi-word** | AND logic | Relevance-based |
| **Stopwords** | No filtering | Filtered automatically |
| **Use case** | Exact matches, filters | Best matches, relevance |

**When to use each:**
- **Regular search:** Filtering by category/tags/date, exact matches
- **FTS search:** Finding "best" matches, multi-word queries, relevance matters

---

## Setup (One-Time)

### Create FTS Index

```bash
cheese-brain create-fts-index
```

**Output:**
```
✅ FTS index created successfully

You can now use: cheese-brain fts 'search query'
```

**What it does:**
- Installs DuckDB FTS extension (if needed)
- Creates full-text index on `entities` table
- Indexes all existing entities

**Time:** ~1 second for 44 entities, ~10 seconds for 10k entities

### Rebuild FTS Index

If entities aren't being found, or after database restore:

```bash
cheese-brain create-fts-index --force
```

---

## Using FTS

### Basic Search

```bash
cheese-brain fts "backup config"
```

**Output:**
```
FTS Search: 'backup config'
┏━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Score ┃ Category ┃ Title              ┃
┡━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 2.413 │ tool     │ Config Backup      │  ← Best match (both words in title)
│       │          │ Script             │
│ 0.976 │ tool     │ Config Restore     │  ← Lower score (1 word in title)
│       │          │ Script             │
│ 0.976 │ workflow │ Config Change      │
│       │          │ Workflow           │
└───────┴──────────┴────────────────────┘

Found 3 results ranked by relevance
```

**Score interpretation:**
- **Higher score = more relevant**
- Score considers: word frequency, document length, term rarity
- Typical range: 0.1 - 3.0 (can go higher with many matches)

### Category Filter

```bash
cheese-brain fts "email" --category project
```

Only searches within the `project` category.

### Limit Results

```bash
cheese-brain fts "scout" --limit 5
```

Returns top 5 most relevant results.

### JSON Output

```bash
cheese-brain fts "gabby" --format json
```

**Output:**
```json
[
  {
    "entity": {
      "id": "8850d8c4-5a9b-4375-8923-db966d86a7ff",
      "category": "project",
      "title": "Gabby Gmail Monitor",
      "tags": ["automation", "nodejs", "gmail"],
      "created_at": "2026-02-17T07:55:53.423998"
    },
    "score": 1.0814682245118305
  }
]
```

---

## Query Tips

### Multi-Word Queries

**Query:** `"gabby email"`

**How it works:**
- Finds documents containing either "gabby" OR "email"
- Ranks documents with BOTH words higher
- Documents with only one word still appear (lower score)

### Stemming

**Query:** `"backup"`

**Matches:**
- "Backup" (exact)
- "Backed" (stem: back)
- "Backing" (stem: back)

### Stopwords

Common words are automatically ignored:
- "the", "a", "an", "and", "or", "but", "is", "are", etc.

**Query:** `"the backup script"` → effectively searches for `"backup script"`

---

## Examples

### Find Email-Related Projects

```bash
cheese-brain fts "email" --category project
```

### Find All Backup Tools

```bash
cheese-brain fts "backup" --category tool
```

### Find Configuration Docs

```bash
cheese-brain fts "config" --category tool
```

### Compare Search Methods

```bash
# Regular search (chronological, exact matches)
cheese-brain search "backup config"

# FTS search (relevance-ranked, stemmed)
cheese-brain fts "backup config"
```

---

## Technical Details

### BM25 Scoring

BM25 (Best Matching 25) is a probabilistic relevance ranking function that considers:

1. **Term Frequency (TF):** How often the query term appears in a document
2. **Inverse Document Frequency (IDF):** How rare the term is across all documents
3. **Document Length:** Shorter documents with matches score higher

**Formula (simplified):**
```
score = IDF(query_term) * (TF * (k1 + 1)) / (TF + k1 * (1 - b + b * (doc_length / avg_doc_length)))
```

Where:
- `k1` = 1.2 (term frequency saturation)
- `b` = 0.75 (length normalization)

**In practice:**
- Exact title matches score highest
- Rare words score higher than common words
- Multiple matching terms multiply the score

### Indexed Fields

FTS searches across:
- **title** (primary field, highest weight)
- **category** (secondary field, medium weight)

**Not indexed:**
- `data` (JSON field - too variable)
- `tags` (use regular search with `--tags`)
- `created_at` (use regular search with `--since`)

### Performance

**Benchmarks (M2 Mac mini):**

| Entities | FTS Index Size | Query Time | vs Regular Search |
|----------|----------------|------------|-------------------|
| 44       | 14 KB          | 5.22 ms    | 10x slower        |
| 10,000   | 343 KB         | 5.22 ms    | Same              |

**Key insight:** FTS has constant-time performance regardless of database size, while regular search scales linearly.

**Break-even point:** ~1,000 entities (FTS becomes faster)

---

## Troubleshooting

### "FTS extension not available"

**Cause:** FTS extension not installed or index not created

**Fix:**
```bash
cheese-brain create-fts-index
```

### No Results Found (But Regular Search Works)

**Cause:** FTS index is stale (not updated with new entities)

**Fix:**
```bash
cheese-brain create-fts-index --force
```

**Note:** FTS index is automatically updated when entities are added/updated/deleted via the CLI. Manual database changes require manual rebuild.

### "FTS index already exists"

**Cause:** Index was created previously

**Options:**
1. Use existing index: `cheese-brain fts "query"`
2. Rebuild index: `cheese-brain create-fts-index --force`

---

## Maintenance

### When to Rebuild FTS Index

Rebuild the index:
- ✅ After restoring from backup
- ✅ If search results seem stale
- ✅ After bulk imports via SQL (not through CLI)
- ❌ NOT needed for normal CLI operations (auto-updated)

### Disk Space

**FTS index overhead:**
- 44 entities: ~14 KB (0.3% of 28 MB database)
- 10,000 entities: ~343 KB (11% of 3 MB data)

**Trade-off:** Minimal space overhead for significant search quality improvement

---

## API Usage (Python)

```python
from cheese_brain import CheeseBrain

brain = CheeseBrain()

# Create FTS index (one-time)
brain.create_fts_index()

# Search with FTS
results = brain.fts_search("backup config", limit=5)

for entity, score in results:
    print(f"[{score:.3f}] {entity.title}")

# Output:
# [2.413] Config Backup Script
# [0.976] Config Restore Script
# [0.976] Config Change Workflow

brain.close()
```

---

## FAQ

### Q: Should I use FTS or regular search?

**A:** Both! They complement each other:
- **FTS:** "Find me the best matches for 'backup config'"
- **Regular search:** "Find all tools tagged 'backup' created after 2026-01-01"

### Q: Does FTS search tags or data fields?

**A:** No, FTS only indexes `title` and `category`. For tag/data searches, use regular search.

### Q: Can I customize stopwords or stemming?

**A:** Currently no. DuckDB FTS uses built-in English stopwords and Porter stemmer. Custom configuration may be added in future versions.

### Q: Does FTS work offline?

**A:** Yes, completely offline. FTS extension is bundled with DuckDB, no external services needed.

---

## Related Documentation

- [README.md](README.md) - Quick start and basic usage
- [WHITEPAPER.md](WHITEPAPER.md) - Technical architecture and benchmarks
- [TODO.md](TODO.md) - Future FTS improvements (custom stopwords, field weighting)

---

**Questions or improvements?** Open an issue on [GitHub](https://github.com/mhugo22/cheese-brain/issues).
