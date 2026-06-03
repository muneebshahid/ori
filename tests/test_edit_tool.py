"""Tests for the default file edit tool."""

from pathlib import Path

import pytest

import agent.tools.edit as edit
from ai.types.tools import ToolResult, ToolTextContent


def test_edit_schema_requires_path_and_edits() -> None:
    """Require a target path and at least one edit collection argument."""

    assert edit.tool.input_schema["required"] == ["path", "edits"]


def test_edit_schema_exposes_edit_controls() -> None:
    """Expose path plus edits inputs."""

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


def test_edit_resolves_relative_path_against_supplied_cwd(tmp_path: Path) -> None:
    """Resolve relative edit paths against the supplied tool cwd."""

    assert edit._resolve_path("sample.txt", tmp_path) == tmp_path / "sample.txt"


def test_edit_expands_home_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Expand home-directory markers in edit paths."""

    monkeypatch.setenv("HOME", str(tmp_path))

    assert edit._resolve_path("~/sample.txt", Path.cwd()) == tmp_path / "sample.txt"


def test_edit_normalizes_unicode_spaces(tmp_path: Path) -> None:
    """Resolve paths typed with uncommon Unicode spaces."""

    file_path = tmp_path / "my file.txt"
    requested_path = str(file_path).replace(" ", "\u00a0")

    assert edit._resolve_path(requested_path, Path.cwd()) == file_path


def test_edit_strips_at_prefix(tmp_path: Path) -> None:
    """Strip leading at signs from referenced edit paths."""

    assert edit._resolve_path("@sample.txt", tmp_path) == tmp_path / "sample.txt"


@pytest.mark.asyncio
async def test_edit_replaces_text_in_file(tmp_path: Path) -> None:
    """Replace a unique exact text block in a file."""

    file_path = _write_text(tmp_path / "sample.txt", "Hello, world!")

    result = _text(
        await edit.fn(
            path=str(file_path),
            edits=[{"oldText": "world", "newText": "testing"}],
            cwd=Path.cwd(),
        )
    )

    assert file_path.read_text(encoding="utf-8") == "Hello, testing!"
    assert result == f"Successfully replaced 1 block(s) in {file_path}."


@pytest.mark.asyncio
async def test_edit_replaces_multiple_disjoint_blocks(tmp_path: Path) -> None:
    """Apply multiple replacements against the original file content."""

    file_path = _write_text(tmp_path / "sample.txt", "alpha\nbeta\ngamma\n")

    await edit.fn(
        path=str(file_path),
        edits=[
            {"oldText": "alpha\n", "newText": "ALPHA\n"},
            {"oldText": "gamma\n", "newText": "GAMMA\n"},
        ],
        cwd=Path.cwd(),
    )

    assert file_path.read_text(encoding="utf-8") == "ALPHA\nbeta\nGAMMA\n"


@pytest.mark.asyncio
async def test_edit_matches_against_original_content(tmp_path: Path) -> None:
    """Match later edits against original content instead of earlier replacements."""

    file_path = _write_text(tmp_path / "sample.txt", "foo\nbar\nbaz\n")

    await edit.fn(
        path=str(file_path),
        edits=[
            {"oldText": "foo\n", "newText": "foo bar\n"},
            {"oldText": "bar\n", "newText": "BAR\n"},
        ],
        cwd=Path.cwd(),
    )

    assert file_path.read_text(encoding="utf-8") == "foo bar\nBAR\nbaz\n"


@pytest.mark.asyncio
async def test_edit_raises_if_text_not_found(tmp_path: Path) -> None:
    """Raise when oldText is not present in the original file."""

    file_path = _write_text(tmp_path / "sample.txt", "Hello, world!")

    with pytest.raises(RuntimeError, match="Could not find the exact text"):
        await edit.fn(
            path=str(file_path),
            edits=[{"oldText": "missing", "newText": "testing"}],
            cwd=Path.cwd(),
        )


@pytest.mark.asyncio
async def test_edit_raises_if_text_is_not_unique(tmp_path: Path) -> None:
    """Raise when oldText appears more than once."""

    file_path = _write_text(tmp_path / "sample.txt", "foo foo foo")

    with pytest.raises(RuntimeError, match="Found 3 occurrences"):
        await edit.fn(
            path=str(file_path),
            edits=[{"oldText": "foo", "newText": "bar"}],
            cwd=Path.cwd(),
        )


@pytest.mark.asyncio
async def test_edit_raises_if_edits_are_empty(tmp_path: Path) -> None:
    """Reject empty edit lists."""

    file_path = _write_text(tmp_path / "sample.txt", "hello\nworld\n")

    with pytest.raises(RuntimeError, match="edits must contain at least one"):
        await edit.fn(path=str(file_path), edits=[], cwd=Path.cwd())


@pytest.mark.asyncio
async def test_edit_raises_if_old_text_is_empty(tmp_path: Path) -> None:
    """Reject empty oldText values."""

    file_path = _write_text(tmp_path / "sample.txt", "hello\nworld\n")

    with pytest.raises(RuntimeError, match="oldText must not be empty"):
        await edit.fn(
            path=str(file_path),
            edits=[{"oldText": "", "newText": "replacement"}],
            cwd=Path.cwd(),
        )


@pytest.mark.asyncio
async def test_edit_raises_if_regions_overlap(tmp_path: Path) -> None:
    """Reject overlapping multi-edit ranges."""

    file_path = _write_text(tmp_path / "sample.txt", "one\ntwo\nthree\n")

    with pytest.raises(RuntimeError, match="overlap"):
        await edit.fn(
            path=str(file_path),
            edits=[
                {"oldText": "one\ntwo\n", "newText": "ONE\nTWO\n"},
                {"oldText": "two\nthree\n", "newText": "TWO\nTHREE\n"},
            ],
            cwd=Path.cwd(),
        )


@pytest.mark.asyncio
async def test_edit_does_not_partially_apply_when_one_edit_fails(
    tmp_path: Path,
) -> None:
    """Leave the file unchanged when any requested edit is invalid."""

    original_content = "alpha\nbeta\ngamma\n"
    file_path = _write_text(tmp_path / "sample.txt", original_content)

    with pytest.raises(RuntimeError, match="Could not find"):
        await edit.fn(
            path=str(file_path),
            edits=[
                {"oldText": "alpha\n", "newText": "ALPHA\n"},
                {"oldText": "missing\n", "newText": "MISSING\n"},
            ],
            cwd=Path.cwd(),
        )

    assert file_path.read_text(encoding="utf-8") == original_content


@pytest.mark.asyncio
async def test_edit_matches_lf_text_and_preserves_crlf(tmp_path: Path) -> None:
    """Match LF oldText against CRLF files and preserve CRLF on write."""

    file_path = _write_text(tmp_path / "sample.txt", "first\r\nsecond\r\nthird\r\n")

    await edit.fn(
        path=str(file_path),
        edits=[{"oldText": "second\n", "newText": "REPLACED\n"}],
        cwd=Path.cwd(),
    )

    assert _read_text(file_path) == "first\r\nREPLACED\r\nthird\r\n"


@pytest.mark.asyncio
async def test_edit_preserves_utf8_bom(tmp_path: Path) -> None:
    """Preserve a leading UTF-8 BOM after editing."""

    file_path = _write_text(tmp_path / "sample.txt", "\ufefffirst\nsecond\nthird\n")

    await edit.fn(
        path=str(file_path),
        edits=[{"oldText": "second\n", "newText": "REPLACED\n"}],
        cwd=Path.cwd(),
    )

    assert file_path.read_text(encoding="utf-8") == "\ufefffirst\nREPLACED\nthird\n"


def _write_text(path: Path, content: str) -> Path:
    """Write test content to a UTF-8 text file."""

    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(content)
    return path


def _read_text(path: Path) -> str:
    """Read test content without newline translation."""

    with path.open("r", encoding="utf-8", newline="") as file:
        return file.read()


def _text(result: ToolResult) -> str:
    """Return the single text block from a tool result."""

    assert len(result.content) == 1
    content = result.content[0]
    assert isinstance(content, ToolTextContent)
    return content.text
