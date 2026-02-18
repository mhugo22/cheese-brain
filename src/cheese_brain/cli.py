"""
CLI interface for Cheese Brain.
"""

import click
import json
import sys
from datetime import datetime
from uuid import UUID
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from cheese_brain.core import CheeseBrain
from cheese_brain.models import Entity, EntityCategory, RelationshipType


console = Console()


@click.group()
@click.pass_context
def main(ctx):
    """🧀 Cheese Brain - DuckDB-powered knowledge management for AI agents and humans."""
    ctx.ensure_object(dict)
    ctx.obj["brain"] = CheeseBrain()


@main.command()
@click.argument("category", type=click.Choice([c.value for c in EntityCategory]))
@click.argument("title")
@click.option("--tags", help="Comma-separated tags")
@click.option("--data", help="JSON data for the entity")
@click.pass_context
def add(ctx, category, title, tags, data):
    """Add a new entity to the knowledge base."""
    brain = ctx.obj["brain"]

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # Parse data
    data_dict = json.loads(data) if data else {}

    # Create entity
    entity = Entity(
        category=EntityCategory(category),
        title=title,
        data=data_dict,
        tags=tag_list,
    )

    entity_id = brain.add_entity(entity)
    console.print(f"✅ Added entity: {entity_id}", style="green")
    console.print(f"   Category: {category}")
    console.print(f"   Title: {title}")
    if tag_list:
        console.print(f"   Tags: {', '.join(tag_list)}")


@main.command()
@click.argument("query")
@click.option("--category", help="Filter by category")
@click.option("--tags", help="Filter by tags (comma-separated, must match ALL)")
@click.option("--since", help="Filter by date (YYYY-MM-DD)")
@click.option("--limit", default=50, help="Maximum results")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--reveal", is_flag=True, help="Show sensitive field values in JSON output")
@click.pass_context
def search(ctx, query, category, tags, since, limit, output_format, reveal):
    """Search entities by keyword."""
    from cheese_brain.redaction import redact_dict
    
    brain = ctx.obj["brain"]

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    # Parse date
    since_dt = datetime.fromisoformat(since) if since else None

    # Search
    results = brain.search(
        query=query,
        category=category,
        tags=tag_list,
        since=since_dt,
        limit=limit,
    )

    if output_format == "json":
        output = []
        for e in results:
            entity_dict = e.model_dump()
            entity_dict["data"] = redact_dict(e.data, reveal=reveal)
            output.append(entity_dict)
        click.echo(json.dumps(output, indent=2, default=str))
    else:
        if not results:
            console.print("No results found.", style="yellow")
            return

        table = Table(title=f"Search Results: '{query}'")
        table.add_column("Category", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Tags", style="dim")
        table.add_column("Created", style="dim")

        for entity in results:
            table.add_row(
                entity.category.value,
                entity.title,
                ", ".join(entity.tags) if entity.tags else "",
                entity.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"\nFound {len(results)} results", style="dim")


@main.command()
@click.argument("query", type=str)
@click.option("--category", help="Filter by category")
@click.option("--limit", default=50, help="Maximum results")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--reveal", is_flag=True, help="Show sensitive field values in JSON output")
@click.pass_context
def fts(ctx, query, category, limit, output_format, reveal):
    """Full-text search with BM25 ranking (faster, relevance-ranked).
    
    Requires FTS index. Create with: cheese-brain create-fts-index
    """
    from cheese_brain.redaction import redact_dict
    
    brain = ctx.obj["brain"]

    try:
        results = brain.fts_search(
            query=query,
            category=category,
            limit=limit,
        )
    except RuntimeError as e:
        console.print(f"❌ {e}", style="red")
        console.print("\nRun: cheese-brain create-fts-index", style="yellow")
        return

    if output_format == "json":
        output = []
        for e, score in results:
            entity_dict = e.model_dump()
            entity_dict["data"] = redact_dict(e.data, reveal=reveal)
            output.append({"entity": entity_dict, "score": score})
        click.echo(json.dumps(output, indent=2, default=str))
    else:
        if not results:
            console.print("No results found.", style="yellow")
            return

        table = Table(title=f"FTS Search: '{query}'")
        table.add_column("Score", style="green")
        table.add_column("Category", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Tags", style="dim")
        table.add_column("Created", style="dim")

        for entity, score in results:
            table.add_row(
                f"{score:.3f}",
                entity.category.value,
                entity.title,
                ", ".join(entity.tags) if entity.tags else "",
                entity.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"\nFound {len(results)} results ranked by relevance", style="dim")


@main.command()
@click.option("--force", is_flag=True, help="Rebuild index if it already exists")
@click.pass_context
def create_fts_index(ctx, force):
    """Create Full-Text Search index for faster keyword searches.
    
    This enables the 'fts' command with BM25 relevance ranking.
    """
    brain = ctx.obj["brain"]

    try:
        created = brain.create_fts_index(force=force)
        if created:
            console.print("✅ FTS index created successfully", style="green")
            console.print("\nYou can now use: cheese-brain fts 'search query'", style="dim")
        else:
            console.print("FTS index already exists. Use --force to rebuild.", style="yellow")
    except RuntimeError as e:
        console.print(f"❌ {e}", style="red")
    except Exception as e:
        console.print(f"❌ Error creating FTS index: {e}", style="red")


@main.command()
@click.option("--category", help="Filter by category")
@click.option("--limit", default=50, help="Maximum results")
@click.option("--deleted", is_flag=True, help="Show deleted entities")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def list(ctx, category, limit, deleted, output_format):
    """List entities."""
    brain = ctx.obj["brain"]

    results = brain.list_entities(
        category=category,
        limit=limit,
        include_deleted=deleted,
    )

    if output_format == "json":
        output = [e.model_dump() for e in results]
        click.echo(json.dumps(output, indent=2, default=str))
    else:
        if not results:
            console.print("No entities found.", style="yellow")
            return

        table = Table(title="Entities")
        table.add_column("ID", style="dim")
        table.add_column("Category", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Tags", style="dim")
        table.add_column("Updated", style="dim")
        if deleted:
            table.add_column("Deleted", style="red")

        for entity in results:
            row = [
                str(entity.id)[:8] + "...",
                entity.category.value,
                entity.title,
                ", ".join(entity.tags) if entity.tags else "",
                entity.updated_at.strftime("%Y-%m-%d %H:%M"),
            ]
            if deleted and entity.deleted_at:
                row.append("✓")
            elif deleted:
                row.append("")

            table.add_row(*row)

        console.print(table)
        console.print(f"\nTotal: {len(results)}", style="dim")


@main.command()
@click.argument("entity_id", type=str)
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--reveal", is_flag=True, help="Show sensitive field values (default: redacted)")
@click.pass_context
def get(ctx, entity_id, output_format, reveal):
    """Get an entity by ID."""
    from cheese_brain.redaction import redact_dict
    
    brain = ctx.obj["brain"]

    try:
        entity = brain.get_by_id(UUID(entity_id))
        if not entity:
            console.print(f"Entity {entity_id} not found.", style="red")
            return

        # Redact sensitive data unless --reveal is set
        display_data = redact_dict(entity.data, reveal=reveal)

        if output_format == "json":
            entity_dict = entity.model_dump()
            entity_dict["data"] = display_data
            click.echo(json.dumps(entity_dict, indent=2, default=str))
        else:
            console.print(f"\n[bold]🧀 {entity.title}[/bold]")
            console.print(f"ID: {entity.id}", style="dim")
            console.print(f"Category: {entity.category.value}")
            console.print(f"Tags: {', '.join(entity.tags) if entity.tags else 'none'}")
            console.print(f"Created: {entity.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"Updated: {entity.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if display_data:
                console.print("\n[bold]Data:[/bold]")
                console.print(json.dumps(display_data, indent=2))
                if not reveal:
                    console.print("\n[dim]Use --reveal to show redacted values[/dim]")

    except ValueError as e:
        console.print(str(e), style="red")


@main.command()
@click.argument("entity_id", type=str)
@click.option("--title", help="New title")
@click.option("--data", help="New JSON data")
@click.option("--add-tags", help="Tags to add (comma-separated)")
@click.pass_context
def update(ctx, entity_id, title, data, add_tags):
    """Update an entity."""
    brain = ctx.obj["brain"]

    try:
        kwargs = {}
        
        if title:
            kwargs["title"] = title
        
        if data:
            kwargs["data"] = json.loads(data)
        
        if add_tags:
            # Get current entity to merge tags
            current = brain.get_by_id(UUID(entity_id))
            if not current:
                console.print(f"Entity {entity_id} not found.", style="red")
                return
            
            new_tags = [t.strip() for t in add_tags.split(",")]
            kwargs["tags"] = list(set(current.tags + new_tags))

        if not kwargs:
            console.print("No updates specified.", style="yellow")
            return

        updated = brain.update(UUID(entity_id), **kwargs)
        console.print(f"✅ Updated entity: {updated.title}", style="green")

    except (ValueError, json.JSONDecodeError) as e:
        console.print(f"Error: {e}", style="red")


@main.command()
@click.argument("entity_id", type=str)
@click.confirmation_option(prompt="Are you sure you want to delete this entity?")
@click.pass_context
def delete(ctx, entity_id):
    """Soft delete an entity."""
    brain = ctx.obj["brain"]

    try:
        brain.delete(UUID(entity_id))
        console.print(f"✅ Deleted entity: {entity_id}", style="green")
        console.print("   (Use 'restore' to recover)", style="dim")
    except ValueError as e:
        console.print(str(e), style="red")


@main.command()
@click.argument("entity_id", type=str)
@click.pass_context
def restore(ctx, entity_id):
    """Restore a soft-deleted entity."""
    brain = ctx.obj["brain"]

    try:
        restored = brain.restore(UUID(entity_id))
        console.print(f"✅ Restored entity: {restored.title}", style="green")
    except ValueError as e:
        console.print(str(e), style="red")


@main.command()
@click.argument("output_path", type=click.Path())
@click.option("--format", type=click.Choice(["json", "parquet"], case_sensitive=False), default="json", help="Export format (json or parquet)")
@click.option("--encrypt", is_flag=True, help="Encrypt export with passphrase (prompts for password)")
@click.pass_context
def export(ctx, output_path, format, encrypt):
    """Export all entities to JSON or Parquet format.
    
    Parquet format provides ~9x compression vs JSON.
    Use --encrypt to password-protect the export file.
    """
    import tempfile
    from cheese_brain.encryption import encrypt_file
    
    brain = ctx.obj["brain"]
    
    # If encrypting, export to temp file first
    if encrypt:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
        export_path = temp_file.name
        temp_file.close()
    else:
        export_path = output_path

    # Export to file (or temp file if encrypting)
    if format.lower() == "parquet":
        count = brain.export_parquet(export_path)
    else:
        count = brain.export_json(export_path)
    
    # Encrypt if requested
    if encrypt:
        passphrase = click.prompt("Encryption passphrase", hide_input=True)
        confirm = click.prompt("Confirm passphrase", hide_input=True)
        
        if passphrase != confirm:
            console.print("❌ Passphrases don't match", style="red")
            os.unlink(export_path)
            return
        
        try:
            encrypt_file(export_path, output_path, passphrase)
            os.unlink(export_path)  # Delete temp file
            console.print(f"✅ Exported and encrypted {count} entities to {output_path}", style="green")
        except Exception as e:
            console.print(f"❌ Encryption failed: {e}", style="red")
            os.unlink(export_path)
            return
    else:
        console.print(f"✅ Exported {count} entities to {output_path} ({format} format)", style="green")


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--merge", is_flag=True, help="Update existing entities instead of erroring")
@click.pass_context
def restore_backup(ctx, input_path, merge):
    """Import entities from JSON or Parquet backup.
    
    Format is auto-detected based on file extension (.json or .parquet).
    Encrypted backups are automatically detected and prompt for passphrase.
    """
    import tempfile
    from cheese_brain.encryption import is_encrypted, decrypt_file
    
    brain = ctx.obj["brain"]
    actual_path = input_path

    try:
        # Check if file is encrypted
        if is_encrypted(input_path):
            console.print("🔒 Encrypted backup detected", style="yellow")
            passphrase = click.prompt("Decryption passphrase", hide_input=True)
            
            # Decrypt to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".decrypted")
            temp_file.close()
            
            try:
                decrypt_file(input_path, temp_file.name, passphrase)
                actual_path = temp_file.name
                console.print("✅ Decryption successful", style="green")
            except ValueError as e:
                console.print(f"❌ {e}", style="red")
                os.unlink(temp_file.name)
                return
        
        # Auto-detect format from file extension (or decrypted content)
        if actual_path.endswith('.parquet') or input_path.endswith('.parquet'):
            count = brain.import_parquet(actual_path, merge=merge)
            console.print(f"✅ Imported {count} entities from {input_path} (Parquet format)", style="green")
        else:
            count = brain.import_json(actual_path, merge=merge)
            console.print(f"✅ Imported {count} entities from {input_path}", style="green")
        
        # Clean up temp file if we decrypted
        if actual_path != input_path and os.path.exists(actual_path):
            os.unlink(actual_path)
            
    except Exception as e:
        console.print(f"Error: {e}", style="red")
        # Clean up temp file on error
        if actual_path != input_path and os.path.exists(actual_path):
            os.unlink(actual_path)


@main.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    brain = ctx.obj["brain"]

    stats = brain.get_stats()

    console.print("\n[bold]📊 Cheese Brain Statistics[/bold]\n")
    console.print(f"Total entities: {stats['total_entities']}")
    console.print(f"Deleted entities: {stats['deleted_entities']}")
    console.print(f"Database size: {stats['db_size_mb']} MB\n")

    if stats["by_category"]:
        table = Table(title="Entities by Category")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="bold")

        for category, count in stats["by_category"].items():
            table.add_row(category, str(count))

        console.print(table)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--format", "input_format", type=click.Choice(["json", "csv"]), help="Input format (auto-detected from extension)")
@click.option("--category", help="Default category for CSV import (if not in file)")
@click.option("--dry-run", is_flag=True, help="Validate without importing")
@click.option("--skip-duplicates", is_flag=True, default=True, help="Skip entities with duplicate titles (default: true)")
@click.option("--merge-duplicates", is_flag=True, help="Update existing entities instead of skipping")
@click.pass_context
def import_bulk(ctx, input_file, input_format, category, dry_run, skip_duplicates, merge_duplicates):
    """Bulk import entities from JSON or CSV file.
    
    JSON Format (array of objects):
    [
        {"category": "tool", "title": "DuckDB", "tags": ["database"], "data": {...}},
        {"category": "project", "title": "My Project", "tags": ["active"], "data": {...}}
    ]
    
    CSV Format:
    title,category,tags,description,url
    DuckDB,tool,"database,analytics",Fast analytics database,https://duckdb.org
    
    Examples:
        cheese-brain import-bulk entities.json
        cheese-brain import-bulk entities.csv --category tool
        cheese-brain import-bulk entities.json --dry-run
        cheese-brain import-bulk entities.csv --merge-duplicates
    """
    brain = ctx.obj["brain"]
    
    # Auto-detect format
    if not input_format:
        if input_file.endswith('.csv'):
            input_format = 'csv'
        else:
            input_format = 'json'
    
    console.print(f"\n📦 Bulk Import: {input_file}", style="bold")
    console.print(f"   Format: {input_format}")
    console.print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    if skip_duplicates:
        console.print(f"   Duplicates: SKIP")
    elif merge_duplicates:
        console.print(f"   Duplicates: MERGE")
    console.print()
    
    try:
        if input_format == 'csv':
            if not category and dry_run:
                # Allow dry-run without category to check CSV
                category = "tool"  # Placeholder
            results = brain.import_csv(
                input_path=input_file,
                category=category,
                dry_run=dry_run,
                skip_duplicates=skip_duplicates if not merge_duplicates else False,
            )
        else:  # json
            with open(input_file, 'r') as f:
                entities = json.load(f)
            
            # Check if entities is a list (using type() to avoid isinstance issues in Click context)
            if not hasattr(entities, '__iter__') or isinstance(entities, (str, dict)):
                console.print("❌ JSON must be an array of entity objects", style="red")
                return
            
            results = brain.bulk_import(
                entities=entities,
                dry_run=dry_run,
                skip_duplicates=skip_duplicates if not merge_duplicates else False,
                merge_duplicates=merge_duplicates,
            )
        
        # Display results
        console.print("[bold green]✅ Import Complete[/bold green]\n")
        
        table = Table(title="Import Results")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="bold")
        
        table.add_row("Total", str(results["total"]))
        table.add_row("Created", str(results["created"]), style="green")
        if results["updated"] > 0:
            table.add_row("Updated", str(results["updated"]), style="yellow")
        if results["skipped"] > 0:
            table.add_row("Skipped", str(results["skipped"]), style="dim")
        if results["errors"]:
            table.add_row("Errors", str(len(results["errors"])), style="red")
        
        console.print(table)
        
        # Show errors if any
        if results["errors"]:
            console.print("\n[bold red]❌ Errors:[/bold red]")
            for idx, error in results["errors"][:10]:  # Show first 10
                console.print(f"   Row {idx + 1}: {error}", style="red")
            if len(results["errors"]) > 10:
                console.print(f"   ... and {len(results['errors']) - 10} more", style="dim")
        
        if dry_run:
            console.print("\n[yellow]ℹ️  This was a dry run. No changes were made.[/yellow]")
        
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        import traceback
        traceback.print_exc()


@main.command()
@click.option("--limit", default=20, help="Number of tags to show")
@click.pass_context
def tags(ctx, limit):
    """Show tag frequency analysis."""
    brain = ctx.obj["brain"]

    # Query tag frequency
    results = brain.conn.execute("""
        SELECT tag, COUNT(*) as cnt
        FROM (SELECT unnest(tags) as tag FROM entities WHERE deleted_at IS NULL)
        GROUP BY tag
        ORDER BY cnt DESC
        LIMIT ?
    """, [limit]).fetchall()

    if not results:
        console.print("No tags found.", style="yellow")
        return

    table = Table(title="Tag Frequency")
    table.add_column("Tag", style="cyan")
    table.add_column("Count", style="bold")

    for tag, count in results:
        table.add_row(tag, str(count))

    console.print(table)


@main.command()
@click.argument("from_id", type=str)
@click.argument("to_id", type=str)
@click.option(
    "--type",
    "rel_type",
    type=click.Choice(["uses", "belongs_to", "requires", "related_to", "depends_on", "documents", "implements"]),
    required=True,
    help="Type of relationship",
)
@click.option("--note", help="Optional note (stored in metadata)")
@click.pass_context
def link(ctx, from_id, to_id, rel_type, note):
    """Create a relationship between two entities.
    
    Examples:
        cheese-brain link <workflow-id> <tool-id> --type uses
        cheese-brain link <email-id> <project-id> --type belongs_to --note "Primary account"
    """
    from cheese_brain.models import RelationshipType
    
    brain = ctx.obj["brain"]
    
    try:
        from_uuid = UUID(from_id)
        to_uuid = UUID(to_id)
        
        metadata = {"note": note} if note else {}
        
        rel_id = brain.add_relationship(
            from_id=from_uuid,
            to_id=to_uuid,
            relationship_type=RelationshipType(rel_type),
            metadata=metadata,
        )
        
        console.print(f"✅ Created relationship: {rel_id}", style="green")
        console.print(f"   From: {from_id}")
        console.print(f"   To: {to_id}")
        console.print(f"   Type: {rel_type}")
        if note:
            console.print(f"   Note: {note}")
            
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@main.command()
@click.argument("relationship_id", type=str)
@click.pass_context
def unlink(ctx, relationship_id):
    """Delete a relationship by ID."""
    brain = ctx.obj["brain"]
    
    try:
        rel_uuid = UUID(relationship_id)
        brain.delete_relationship(rel_uuid)
        console.print(f"✅ Deleted relationship: {relationship_id}", style="green")
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@main.command()
@click.argument("entity_id", type=str)
@click.option(
    "--direction",
    type=click.Choice(["from", "to", "both"]),
    default="both",
    help="Show relationships from/to this entity (default: both)",
)
@click.option(
    "--type",
    "rel_type",
    type=click.Choice(["uses", "belongs_to", "requires", "related_to", "depends_on", "documents", "implements"]),
    help="Filter by relationship type",
)
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def links(ctx, entity_id, direction, rel_type, output_format):
    """Show all relationships for an entity.
    
    Examples:
        cheese-brain links <entity-id>
        cheese-brain links <entity-id> --direction from
        cheese-brain links <entity-id> --type uses
    """
    from cheese_brain.models import RelationshipType
    
    brain = ctx.obj["brain"]
    
    try:
        entity_uuid = UUID(entity_id)
        
        # Get entity to show context
        entity = brain.get_by_id(entity_uuid)
        if not entity:
            console.print(f"❌ Entity {entity_id} not found", style="red")
            return
        
        # Get relationships
        rel_type_enum = RelationshipType(rel_type) if rel_type else None
        relationships = brain.get_relationships(
            entity_id=entity_uuid,
            direction=direction,
            relationship_type=rel_type_enum,
        )
        
        if output_format == "json":
            output = []
            for rel, related_entity in relationships:
                output.append({
                    "relationship_id": str(rel.id),
                    "from_id": str(rel.from_id),
                    "to_id": str(rel.to_id),
                    "type": rel.relationship_type.value,
                    "metadata": rel.metadata,
                    "related_entity": {
                        "id": str(related_entity.id),
                        "category": related_entity.category.value,
                        "title": related_entity.title,
                        "tags": related_entity.tags,
                    },
                })
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            console.print(f"\n📎 Relationships for: {entity.title}", style="bold cyan")
            console.print(f"   Category: {entity.category.value}")
            console.print(f"   ID: {entity_id}\n")
            
            if not relationships:
                console.print("No relationships found.", style="yellow")
                return
            
            table = Table(title=f"Relationships ({len(relationships)} total)")
            table.add_column("Direction", style="dim")
            table.add_column("Type", style="cyan")
            table.add_column("Related Entity", style="bold")
            table.add_column("Category", style="dim")
            table.add_column("Rel ID", style="dim")
            
            for rel, related_entity in relationships:
                # Determine direction arrow
                if rel.from_id == entity_uuid:
                    direction_arrow = "→"
                else:
                    direction_arrow = "←"
                
                table.add_row(
                    direction_arrow,
                    rel.relationship_type.value,
                    related_entity.title,
                    related_entity.category.value,
                    str(rel.id)[:8] + "...",
                )
            
            console.print(table)
            
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@main.command()
@click.argument("entity_id", type=str)
@click.option("--depth", default=1, type=int, help="Depth of graph traversal (default: 1)")
@click.option(
    "--type",
    "rel_type",
    type=click.Choice(["uses", "belongs_to", "requires", "related_to", "depends_on", "documents", "implements"]),
    help="Filter by relationship type",
)
@click.option("--format", "output_format", type=click.Choice(["tree", "json"]), default="tree")
@click.pass_context
def graph(ctx, entity_id, depth, rel_type, output_format):
    """Show relationship graph starting from an entity.
    
    Examples:
        cheese-brain graph <entity-id>
        cheese-brain graph <entity-id> --depth 2
        cheese-brain graph <entity-id> --type uses
    """
    from cheese_brain.models import RelationshipType
    
    brain = ctx.obj["brain"]
    
    try:
        entity_uuid = UUID(entity_id)
        rel_type_enum = RelationshipType(rel_type) if rel_type else None
        
        graph_data = brain.get_relationship_graph(
            entity_id=entity_uuid,
            depth=depth,
            relationship_type=rel_type_enum,
        )
        
        if output_format == "json":
            output = {
                "entity": {
                    "id": str(graph_data["entity"].id),
                    "category": graph_data["entity"].category.value,
                    "title": graph_data["entity"].title,
                },
                "relationships": []
            }
            for rel in graph_data["relationships"]:
                output["relationships"].append({
                    "type": rel["type"],
                    "direction": rel["direction"],
                    "depth": rel["depth"],
                    "relationship_id": rel["relationship_id"],
                    "related": {
                        "id": str(rel["related"].id),
                        "category": rel["related"].category.value,
                        "title": rel["related"].title,
                    },
                })
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            entity = graph_data["entity"]
            relationships = graph_data["relationships"]
            
            console.print(f"\n🔗 Relationship Graph", style="bold cyan")
            console.print(f"\n📍 Root: {entity.title}", style="bold")
            console.print(f"   Category: {entity.category.value}")
            console.print(f"   ID: {entity_id}\n")
            
            if not relationships:
                console.print("No relationships found.", style="yellow")
                return
            
            # Group by relationship type
            by_type = {}
            for rel in relationships:
                rel_type = rel["type"]
                if rel_type not in by_type:
                    by_type[rel_type] = []
                by_type[rel_type].append(rel)
            
            for rel_type, rels in by_type.items():
                console.print(f"\n{rel_type.upper()}", style="cyan bold")
                for rel in rels:
                    arrow = "  →" if rel["direction"] == "from" else "  ←"
                    console.print(
                        f"{arrow} {rel['related'].title} "
                        f"({rel['related'].category.value})",
                        style="dim" if rel['direction'] == "to" else "white"
                    )
            
            console.print(f"\nTotal relationships: {len(relationships)}", style="dim")
            
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


if __name__ == "__main__":
    main(obj={})
