"""Provider stream helpers for stateless agent tests."""

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from agent.types import StreamFn
from ai.types.contracts import Reasoning
from ai.types.conversation import ConversationItem
from ai.types.stream_events import ProviderStreamEvent
from ai.types.tools import ToolDefinition
from tests.support.async_streams import async_stream


@dataclass
class StreamInvocation:
    """Captured arguments from one provider stream invocation."""

    history: tuple[ConversationItem, ...]
    model: str
    instructions: str
    reasoning: Reasoning | None
    tools: tuple[ToolDefinition, ...] | None


def build_stream_fn(
    streams: Sequence[Sequence[ProviderStreamEvent]],
    invocations: list[StreamInvocation],
) -> StreamFn:
    """Build a provider stream function that records each invocation."""

    pending_streams = list(streams)

    async def _stream_fn(
        history: Sequence[ConversationItem],
        model: str,
        *,
        instructions: str,
        reasoning: Reasoning | None,
        tools: Sequence[ToolDefinition] | None,
    ) -> AsyncIterator[ProviderStreamEvent]:
        """Return the next queued provider event stream."""

        invocations.append(
            StreamInvocation(
                history=tuple(history),
                model=model,
                instructions=instructions,
                reasoning=reasoning,
                tools=tuple(tools) if tools is not None else None,
            )
        )
        return async_stream(pending_streams.pop(0))

    return _stream_fn
