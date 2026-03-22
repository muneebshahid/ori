from collections.abc import Awaitable, Sequence
from typing import Protocol

from ai.contracts import AsyncEventStream, Reasoning
from ai.conversation import (
    AssistantReasoningBlock,
    AssistantTextBlock,
    AssistantTurn,
    ConversationItem,
    UserMessage,
)
from ai.types import (
    AssistantMessage,
    ReasoningDeltaEvent,
    ReasoningBlock,
    ReasoningEndEvent,
    ReasoningStartEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    StreamEvent,
    StreamStartEvent,
    TextBlock,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
)
from agent.prompt import PROMPT


class StreamFn(Protocol):
    def __call__(
        self,
        history: Sequence[ConversationItem],
        model: str,
        *,
        instructions: str,
        reasoning: Reasoning | None,
    ) -> Awaitable[AsyncEventStream]: ...


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
            case StreamDoneEvent():
                await self._handle_stream_done_event(event)
            case StreamErrorEvent():
                await self._handle_stream_error_event(event)
            case (
                StreamStartEvent()
                | ReasoningStartEvent()
                | ReasoningDeltaEvent()
                | ReasoningEndEvent()
                | TextStartEvent()
                | TextDeltaEvent()
                | TextEndEvent()
            ):
                return None
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
        content=[_build_assistant_block(block) for block in message.content],
        response_id=message.response_id,
    )


def _build_assistant_block(
    block: TextBlock | ReasoningBlock,
) -> AssistantTextBlock | AssistantReasoningBlock:
    match block:
        case TextBlock():
            return AssistantTextBlock(
                text=block.text,
                message_id=block.message_id,
                phase=block.phase,
            )
        case ReasoningBlock():
            return AssistantReasoningBlock(
                summary_text=block.reasoning,
                reasoning_id=block.reasoning_id,
            )
