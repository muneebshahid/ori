import pytest
from pydantic import ValidationError

from ai.types.tools import ToolDefinition


def test_tool_definition_rejects_non_json_schema_values() -> None:
    with pytest.raises(ValidationError):
        ToolDefinition.model_validate(
            {
                "name": "ls",
                "description": "List the contents of a directory.",
                "input_schema": {
                    "type": object(),
                },
            }
        )
