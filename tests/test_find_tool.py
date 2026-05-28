"""Tests for the default file path search tool scaffold."""

import agent.tools.find as find


def test_find_schema_requires_only_pattern() -> None:
    """Require only the glob pattern so callers can omit optional controls."""

    assert find.tool.input_schema["required"] == ["pattern"]


def test_find_schema_exposes_path_search_controls() -> None:
    """Expose the path-search inputs without execution-specific fields."""

    properties = find.tool.input_schema["properties"]

    assert find.tool.name == "find"
    assert isinstance(properties, dict)
    assert set(properties) == {"pattern", "path", "limit"}
