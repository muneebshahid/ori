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
from agent.types import StreamFn


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

    async def run(self, prompt: str) -> None:
        self._history.append(UserMessage(content=prompt))
        stream = await self._stream_fn(
            self._history,
            self._model,
            instructions=self._system_prompt,
            reasoning=self._reasoning,
        )

        async for event in stream:
            await self._dispatch_event(event)

    async def _dispatch_event(self, event: StreamEvent) -> None:
        match event:
            case (
                StreamStartEvent()
                | ReasoningStartEvent()
                | ReasoningDeltaEvent()
                | ReasoningEndEvent()
                | TextStartEvent()
                | TextDeltaEvent()
                | TextEndEvent()
                | ToolCallStartEvent()
                | ToolCallDeltaEvent()
                | ToolCallEndEvent()
            ):
                return None
            case StreamDoneEvent():
                await self._handle_stream_done_event(event)
            case StreamErrorEvent():
                await self._handle_stream_error_event(event)

            case _:
                return None

    async def _handle_stream_done_event(
        self,
        event: StreamDoneEvent,
    ) -> None:
        self._history.append(_build_assistant_turn(event.message))
        return None

    async def _handle_stream_error_event(
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
