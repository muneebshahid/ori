"""Tests for the local headless command runner."""

import asyncio
import io
import json
from collections.abc import AsyncIterator, Sequence

from agent.agent import Agent
from ai.types.contracts import Reasoning
from ai.types.conversation import ConversationItem, UserMessage
from ai.types.stream import (
    AssistantMessage,
    StreamDoneEvent,
    StreamEvent,
    StreamStartEvent,
)
from ai.types.tools import ToolDefinition
from main import run_cli, run_prompt


def test_run_prompt_streams_agent_events_as_json_lines() -> None:
    """Run one prompt through the local runner with a deterministic agent."""

    agent = _build_agent([_start_event(), _done_event()])
    output = io.StringIO()

    asyncio.run(run_prompt("Hello from CLI", agent=agent, output=output))

    lines = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [line["type"] for line in lines] == [
        "agent_start",
        "turn_start",
        "message_start",
        "message_end",
        "turn_end",
        "agent_end",
    ]
    assert len(agent.history) == 2
    user_message = agent.history[0]
    assert isinstance(user_message, UserMessage)
    assert user_message.content == "Hello from CLI"


def test_run_cli_rejects_empty_prompt() -> None:
    """Reject a missing prompt before constructing the default agent."""

    status = asyncio.run(run_cli(["   "]))

    assert status == 2


def _build_agent(stream_events: Sequence[StreamEvent]) -> Agent:
    """Build an agent whose provider returns static stream events."""

    async def _stream_fn(
        history: Sequence[ConversationItem],
        model: str,
        *,
        instructions: str,
        reasoning: Reasoning | None,
        tools: Sequence[ToolDefinition] | None,
    ) -> AsyncIterator[StreamEvent]:
        """Return the static event stream expected by ``Agent``."""

        _ = history, model, instructions, reasoning, tools
        return _iter_stream_events(stream_events)

    return Agent(stream_fn=_stream_fn, model="gpt-5.4")


def _iter_stream_events(
    stream_events: Sequence[StreamEvent],
) -> AsyncIterator[StreamEvent]:
    """Yield static stream events asynchronously."""

    async def _iterate() -> AsyncIterator[StreamEvent]:
        for event in stream_events:
            yield event

    return _iterate()


def _start_event() -> StreamStartEvent:
    """Build a deterministic stream start event."""

    return StreamStartEvent(
        type="start",
        message=AssistantMessage(response_id="resp_cli"),
    )


def _done_event() -> StreamDoneEvent:
    """Build a deterministic stream completion event."""

    return StreamDoneEvent(
        type="done",
        message=AssistantMessage(response_id="resp_cli"),
    )
