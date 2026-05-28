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


def test_build_args_uses_default_file_search_flags() -> None:
    """Build the default argv for file path search output."""

    assert find._build_args(pattern="*.py", path=".", limit=1000) == [
        "--glob",
        "--color=never",
        "--hidden",
        "--no-require-git",
        "--max-results",
        "1000",
        "--",
        "*.py",
        ".",
    ]


def test_build_args_uses_full_path_for_path_patterns() -> None:
    """Match path-shaped glob patterns against full candidate paths."""

    assert find._build_args(pattern="agent/**/*.py", path=".", limit=25) == [
        "--glob",
        "--color=never",
        "--hidden",
        "--no-require-git",
        "--max-results",
        "25",
        "--full-path",
        "--",
        "**/agent/**/*.py",
        ".",
    ]


def test_build_args_normalizes_root_relative_full_path_pattern() -> None:
    """Treat leading-slash glob patterns as search-root-relative paths."""

    assert find._build_args(pattern="/tools/*.py", path=".", limit=25)[-3:] == [
        "--",
        "**/tools/*.py",
        ".",
    ]


def test_build_args_preserves_prefixed_full_path_pattern() -> None:
    """Do not double-prefix full-path glob patterns."""

    assert find._build_args(pattern="**/tools/*.py", path=".", limit=25)[-3:] == [
        "--",
        "**/tools/*.py",
        ".",
    ]


def test_build_args_clamps_limit_to_one() -> None:
    """Keep fd max-results positive even when callers pass a low limit."""

    assert find._build_args(pattern="*.py", path=".", limit=0)[4:6] == [
        "--max-results",
        "1",
    ]
