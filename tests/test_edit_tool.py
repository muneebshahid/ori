"""Tests for the default file edit tool scaffold."""

from pathlib import Path

import pytest

import agent.tools.edit as edit


def test_edit_schema_requires_path_and_edits() -> None:
    """Require a target path and at least one edit collection argument."""

    assert edit.tool.input_schema["required"] == ["path", "edits"]


def test_edit_schema_exposes_pi_style_edit_controls() -> None:
    """Expose Pi-style path plus edits inputs."""

    properties = edit.tool.input_schema["properties"]

    assert edit.tool.name == "edit"
    assert isinstance(properties, dict)
    assert set(properties) == {"path", "edits"}


def test_edit_schema_describes_each_replacement() -> None:
    """Expose oldText and newText for every edit item."""

    properties = edit.tool.input_schema["properties"]
    assert isinstance(properties, dict)

    edits_schema = properties["edits"]
    assert isinstance(edits_schema, dict)

    item_schema = edits_schema["items"]
    assert isinstance(item_schema, dict)

    item_properties = item_schema["properties"]
    assert isinstance(item_properties, dict)

    assert set(item_properties) == {"oldText", "newText"}
    assert item_schema["required"] == ["oldText", "newText"]
    assert item_schema["additionalProperties"] is False
