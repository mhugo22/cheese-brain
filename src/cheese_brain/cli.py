"""
CLI interface for Cheese Brain.
"""

import click
import json
from datetime import datetime
from uuid import UUID
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from cheese_brain.core import CheeseBrain
from cheese_brain.models import Entity, EntityCategory


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
@click.pass_context
def search(ctx, query, category, tags, since, limit, output_format):
    """Search entities by keyword."""
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
        output = [e.model_dump() for e in results]
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
@click.pass_context
def get(ctx, entity_id, output_format):
    """Get an entity by ID."""
    brain = ctx.obj["brain"]

    try:
        entity = brain.get_by_id(UUID(entity_id))
        if not entity:
            console.print(f"Entity {entity_id} not found.", style="red")
            return

        if output_format == "json":
            click.echo(json.dumps(entity.model_dump(), indent=2, default=str))
        else:
            console.print(f"\n[bold]🧀 {entity.title}[/bold]")
            console.print(f"ID: {entity.id}", style="dim")
            console.print(f"Category: {entity.category.value}")
            console.print(f"Tags: {', '.join(entity.tags) if entity.tags else 'none'}")
            console.print(f"Created: {entity.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"Updated: {entity.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if entity.data:
                console.print("\n[bold]Data:[/bold]")
                console.print(json.dumps(entity.data, indent=2))

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
@click.pass_context
def export(ctx, output_path, format):
    """Export all entities to JSON or Parquet format.
    
    Parquet format provides ~9x compression vs JSON.
    """
    brain = ctx.obj["brain"]

    if format.lower() == "parquet":
        count = brain.export_parquet(output_path)
        console.print(f"✅ Exported {count} entities to {output_path} (Parquet format)", style="green")
    else:
        count = brain.export_json(output_path)
        console.print(f"✅ Exported {count} entities to {output_path}", style="green")


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--merge", is_flag=True, help="Update existing entities instead of erroring")
@click.pass_context
def restore_backup(ctx, input_path, merge):
    """Import entities from JSON or Parquet backup.
    
    Format is auto-detected based on file extension (.json or .parquet).
    """
    brain = ctx.obj["brain"]

    try:
        # Auto-detect format from file extension
        if input_path.endswith('.parquet'):
            count = brain.import_parquet(input_path, merge=merge)
            console.print(f"✅ Imported {count} entities from {input_path} (Parquet format)", style="green")
        else:
            count = brain.import_json(input_path, merge=merge)
            console.print(f"✅ Imported {count} entities from {input_path}", style="green")
    except Exception as e:
        console.print(f"Error: {e}", style="red")


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
@click.option("--limit", default=20, help="Number of tags to show")
@click.pass_context
def tags(ctx, limit):
    """Show tag frequency analysis."""
    brain = ctx.obj["brain"]

    # Query tag frequency
    results = brain.conn.execute(f"""
        SELECT tag, COUNT(*) as cnt
        FROM (SELECT unnest(tags) as tag FROM entities WHERE deleted_at IS NULL)
        GROUP BY tag
        ORDER BY cnt DESC
        LIMIT {limit}
    """).fetchall()

    if not results:
        console.print("No tags found.", style="yellow")
        return

    table = Table(title="Tag Frequency")
    table.add_column("Tag", style="cyan")
    table.add_column("Count", style="bold")

    for tag, count in results:
        table.add_row(tag, str(count))

    console.print(table)


if __name__ == "__main__":
    main(obj={})
