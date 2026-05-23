"""Tests for the default search tool scaffold."""

from agent.tools.grep import grep


def test_grep_schema_requires_only_pattern() -> None:
    """Require only the search pattern so callers can omit optional controls."""

    assert grep.input_schema["required"] == ["pattern"]
