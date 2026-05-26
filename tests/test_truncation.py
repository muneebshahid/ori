"""Tests for shared tool output truncation helpers."""

import agent.tools.truncation as truncation


def test_truncate_to_byte_limit_keeps_complete_lines() -> None:
    """Truncate over-limit output at line boundaries instead of mid-line."""

    assert truncation.truncate_to_byte_limit("a.txt\nb.txt", byte_limit=11) == (
        "a.txt\nb.txt",
        False,
    )
    assert truncation.truncate_to_byte_limit("a.txt\nb.txt", byte_limit=10) == (
        "a.txt",
        True,
    )
