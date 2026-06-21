"""Stateless agent run loop for provider streams and tool execution."""

from collections.abc import AsyncIterator, Sequence
from pathlib import Path

from ai.types.contracts import Reasoning
from ai.types.conversation import AssistantTurn, ConversationItem, ToolResultTurn
from ai.types.stream_events import (
    AssistantBlock,
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    ReasoningStartEvent,
    ProviderStreamEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    StreamStartEvent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
    ToolCallBlock,
    ToolCallDeltaEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)
from ai.types.tools import JsonObject, ToolDefinition, ToolFunction, ToolResult
from agent.prompt import PROMPT, build_system_prompt
from agent.types import (
    AgentEndEvent,
    AgentEvent,
    AgentStartEvent,
    MessageEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    StreamFn,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    TurnEndEvent,
    TurnStartEvent,
)

ASSISTANT_MESSAGE_UPDATE_EVENT_TYPES = (
    ReasoningStartEvent,
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    TextStartEvent,
    TextDeltaEvent,
    TextEndEvent,
    ToolCallStartEvent,
    ToolCallDeltaEvent,
    ToolCallEndEvent,
)


async def run_agent(
    history: Sequence[ConversationItem],
    *,
    stream_fn: StreamFn,
    model: str,
    reasoning: Reasoning | None = None,
    tools: Sequence[ToolDefinition] = (),
    system_prompt: str = PROMPT,
    cwd: Path | str | None = None,
) -> AsyncIterator[AgentEvent]:
    """Run one stateless agent turn from supplied model-visible history."""

    run_history = list(history)
    instructions = build_system_prompt(system_prompt, _resolve_cwd(cwd))

    yield AgentStartEvent()
    async for event in _run_agent_loop(
        run_history=run_history,
        stream_fn=stream_fn,
        model=model,
        instructions=instructions,
        reasoning=reasoning,
        tools=tuple(tools),
    ):
        yield event
    yield AgentEndEvent()


async def _run_agent_loop(
    *,
    run_history: list[ConversationItem],
    stream_fn: StreamFn,
    model: str,
    instructions: str,
    reasoning: Reasoning | None,
    tools: tuple[ToolDefinition, ...],
) -> AsyncIterator[AgentEvent]:
    """Call the provider until the assistant stops requesting tools."""

    while True:
        has_tool_results = False
        stream = await stream_fn(
            tuple(run_history),
            model,
            instructions=instructions,
            reasoning=reasoning,
            tools=tools,
        )

        async for event in stream:
            async for agent_event in _handle_stream_event(
                event,
                run_history=run_history,
                tools=tools,
            ):
                if (
                    isinstance(agent_event, TurnEndEvent)
                    and agent_event.tool_result_turns
                ):
                    has_tool_results = True
                yield agent_event

        if not has_tool_results:
            break


async def _handle_stream_event(
    event: ProviderStreamEvent,
    *,
    run_history: list[ConversationItem],
    tools: tuple[ToolDefinition, ...],
) -> AsyncIterator[AgentEvent]:
    """Route one provider stream event into agent-level events."""

    match event:
        case StreamStartEvent():
            yield TurnStartEvent()
            yield MessageStartEvent(response_id=event.response_id)
        case StreamDoneEvent():
            async for agent_event in _handle_stream_done_event(
                event,
                run_history=run_history,
                tools=tools,
            ):
                yield agent_event
        case StreamErrorEvent():
            async for agent_event in _handle_stream_error_event(
                event,
                run_history=run_history,
            ):
                yield agent_event
        case _ if isinstance(event, ASSISTANT_MESSAGE_UPDATE_EVENT_TYPES):
            yield MessageUpdateEvent(stream_event=event)


async def _handle_stream_done_event(
    event: StreamDoneEvent,
    *,
    run_history: list[ConversationItem],
    tools: tuple[ToolDefinition, ...],
) -> AsyncIterator[AgentEvent]:
    """Finalize an assistant message and execute requested tools."""

    turn = AssistantTurn.from_stream_done(event)
    run_history.append(turn)
    yield MessageEndEvent(assistant_turn=turn)
    tool_results: list[ToolResultTurn] = []

    for tool_call in _collect_tool_calls(turn.blocks):
        async for agent_event in _execute_tool(
            call_id=tool_call.call_id,
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
            tools=tools,
        ):
            if isinstance(agent_event, ToolExecutionEndEvent):
                tool_result = agent_event.tool_result_turn
                run_history.append(tool_result)
                tool_results.append(tool_result)
            yield agent_event

    yield TurnEndEvent(assistant_turn=turn, tool_result_turns=tool_results)


async def _handle_stream_error_event(
    event: StreamErrorEvent,
    *,
    run_history: list[ConversationItem],
) -> AsyncIterator[AgentEvent]:
    """Finalize a failed assistant message."""

    turn = AssistantTurn.from_stream_error(event)
    run_history.append(turn)
    yield MessageEndEvent(assistant_turn=turn)
    yield TurnEndEvent(assistant_turn=turn, tool_result_turns=[])


async def _execute_tool(
    *,
    call_id: str,
    tool_name: str,
    arguments: JsonObject,
    tools: tuple[ToolDefinition, ...],
) -> AsyncIterator[AgentEvent]:
    """Emit the full lifecycle for one tool execution."""

    yield ToolExecutionStartEvent(
        call_id=call_id,
        tool_name=tool_name,
        arguments=arguments,
    )

    result, is_error = await _call_tool(tool_name, arguments, tools)
    tool_result_turn = ToolResultTurn(
        call_id=call_id,
        tool_name=tool_name,
        content=result.content,
        is_error=is_error,
    )
    yield ToolExecutionEndEvent(
        call_id=call_id,
        tool_name=tool_name,
        result=result,
        is_error=is_error,
        tool_result_turn=tool_result_turn,
    )


async def _call_tool(
    tool_name: str,
    arguments: JsonObject,
    tools: tuple[ToolDefinition, ...],
) -> tuple[ToolResult, bool]:
    """Resolve and call a tool while normalizing tool failures."""

    try:
        tool = _get_tool(tool_name, tools)
        if tool is None:
            return ToolResult.text(f"Tool '{tool_name}' not found"), True
        return await tool(**arguments), False
    except Exception as error:
        return ToolResult.text(str(error)), True


def _get_tool(
    tool_name: str,
    tools: tuple[ToolDefinition, ...],
) -> ToolFunction | None:
    """Find a registered tool implementation by name."""

    normalized_tool_name = tool_name.lower().strip()
    for tool in tools:
        if tool.name == normalized_tool_name:
            return tool.fn
    return None


def _resolve_cwd(cwd: Path | str | None) -> Path:
    """Resolve the agent working directory."""

    if cwd is None:
        return Path.cwd().resolve()
    return Path(cwd).expanduser().resolve()


def _collect_tool_calls(blocks: Sequence[AssistantBlock]) -> list[ToolCallBlock]:
    """Collect tool calls from finalized assistant blocks."""

    return [
        block.model_copy(deep=True)
        for block in blocks
        if isinstance(block, ToolCallBlock)
    ]
