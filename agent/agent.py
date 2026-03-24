from collections.abc import AsyncIterator
from collections.abc import Sequence
from ai.types.contracts import Reasoning
from ai.types.conversation import (
    AssistantTurn,
    ConversationItem,
    UserMessage,
)
from ai.types.stream import (
    AssistantMessage,
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    ReasoningStartEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    StreamEvent,
    StreamStartEvent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
    ToolCallDeltaEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)
from agent.prompt import PROMPT
from agent.types import (
    StreamFn,
    AgentStartEvent,
    AgentEndEvent,
    TurnEndEvent,
    AgentEvent,
    TurnStartEvent,
)

IGNORED_STREAM_EVENT_TYPES = (
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


class AgentRunError(RuntimeError):
    """Raised when the provider stream ends with an error event."""


class Agent:
    def __init__(
        self,
        stream_fn: StreamFn,
        model: str,
        reasoning: Reasoning | None = None,
        history: Sequence[ConversationItem] | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._stream_fn = stream_fn
        self._model = model
        self._reasoning = reasoning
        self._history = list(history or [])
        self._system_prompt = system_prompt or PROMPT

    def update_model(self, model: str) -> None:
        self._model = model

    def update_reasoning(self, reasoning: Reasoning | None) -> None:
        self._reasoning = reasoning

    @property
    def history(self) -> Sequence[ConversationItem]:
        return tuple(self._history)

    def replace_history(self, history: Sequence[ConversationItem]) -> None:
        self._history = list(history)

    def add_item(self, item: ConversationItem) -> None:
        self._history.append(item)

    async def run(self, prompt: str) -> AsyncIterator[AgentEvent]:
        yield AgentStartEvent()
        async for event in self._run_stream(prompt):
            yield event
        yield AgentEndEvent(items=self._history)

    async def _run_stream(self, prompt: str) -> AsyncIterator[AgentEvent]:
        self._history.append(UserMessage(content=prompt))
        stream = await self._stream_fn(
            self._history,
            self._model,
            instructions=self._system_prompt,
            reasoning=self._reasoning,
        )

        async for event in stream:
            async for agent_event in self._emit_events_for(event):
                yield agent_event

    async def _emit_events_for(self, event: StreamEvent) -> AsyncIterator[AgentEvent]:
        if handler := self._select_event_handler(event):
            async for agent_event in handler:
                yield agent_event

    def _select_event_handler(
        self,
        event: StreamEvent,
    ) -> AsyncIterator[AgentEvent] | None:
        match event:
            case StreamStartEvent():
                return self._handle_stream_start_event(event)
            case StreamDoneEvent():
                return self._handle_stream_done_event(event)
            case StreamErrorEvent():
                return self._handle_stream_error_event(event)
            case _ if isinstance(event, IGNORED_STREAM_EVENT_TYPES):
                return None

        return None

    async def _handle_stream_start_event(
        self,
        event: StreamStartEvent,
    ) -> AsyncIterator[AgentEvent]:
        yield TurnStartEvent()

    async def _handle_stream_done_event(
        self,
        event: StreamDoneEvent,
    ) -> AsyncIterator[AgentEvent]:
        message = _build_assistant_turn(event.message)
        self._history.append(message)
        yield TurnEndEvent(message=message, tool_results=[])

    def _handle_stream_error_event(
        self,
        event: StreamErrorEvent,
    ) -> None:
        raise AgentRunError(event.message)


def _build_assistant_turn(message: AssistantMessage) -> AssistantTurn:
    return AssistantTurn(
        content=[block.model_copy(deep=True) for block in message.content],
        response_id=message.response_id,
        stop_reason=message.stop_reason,
    )
