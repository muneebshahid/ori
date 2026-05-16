"""Shared request builders for OpenAI response-stream transports."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from openai.types.responses.response_create_params import (
    ResponseCreateParamsStreaming,
)

from ai.openai.serialization import serialize_history_items, serialize_tools
from ai.types.contracts import Reasoning as AppReasoning
from ai.types.conversation import ConversationItem
from ai.types.tools import ToolDefinition

if TYPE_CHECKING:
    from openai.types.shared_params.reasoning import Reasoning as OpenAIReasoning


def build_stream_request_params(
    history: Sequence[ConversationItem],
    model: str,
    *,
    instructions: str,
    reasoning: AppReasoning | None = None,
    tools: Sequence[ToolDefinition] | None = None,
) -> ResponseCreateParamsStreaming:
    """Build the shared Responses API request payload for stream transports."""

    request_params: ResponseCreateParamsStreaming = {
        "model": model,
        "input": serialize_history_items(history),
        "reasoning": cast("OpenAIReasoning | None", reasoning),
        "instructions": instructions,
        "stream": True,
    }
    if tools:
        request_params["tools"] = serialize_tools(tools)
    return request_params
