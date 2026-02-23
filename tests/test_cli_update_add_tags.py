import json
from uuid import UUID

from click.testing import CliRunner

from cheese_brain.cli import main
from cheese_brain.core import CheeseBrain
from cheese_brain.models import Entity, EntityCategory


def test_cli_update_add_tags_does_not_break_on_list_command_name_collision():
    """Regression test.

    Previously the CLI had a command function named `list`, which shadowed the
    Python built-in `list` in module scope. The `update` command used `list(...)`
    when merging tags, which ended up calling the Click command instead of the
    built-in, causing: "Got unexpected extra arguments".
    """

    brain = CheeseBrain()
    entity = Entity(category=EntityCategory.TOOL, title="CliUpdateTagTest", tags=["a", "b"], data={})
    entity_id = brain.add_entity(entity)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["update", str(entity_id), "--add-tags", "c"],
        obj={"brain": brain},
    )

    assert result.exit_code == 0, result.output

    updated = brain.get_by_id(UUID(str(entity_id)))
    assert updated is not None
    assert set(updated.tags) == {"a", "b", "c"}

    brain.delete(entity_id)
