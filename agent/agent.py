from dataclasses import dataclass, field
from collections.abc import Awaitable
from typing import Callable

from openai.types.responses.response_created_event import ResponseCreatedEvent
from openai.types.responses.response_in_progress_event import ResponseInProgressEvent
from openai.types.responses.response_output_item_added_event import (
    ResponseOutputItemAddedEvent,
)
from ai.contracts import AsyncEventStream, Reasoning


@dataclass
class AgentState:
    model: str
    reasoning: Reasoning | None = None
    messages: list[object] = field(default_factory=list)


StreamFn = Callable[[str, str, Reasoning | None], Awaitable[AsyncEventStream]]


class Agent:
    def __init__(
        self,
        stream_fn: StreamFn,
        model: str,
        reasoning: Reasoning | None = None,
        messages: list[object] | None = None,
    ) -> None:
        self._stream_fn = stream_fn
        self._state = AgentState(
            model=model,
            reasoning=reasoning,
            messages=list(messages or []),
        )

    @property
    def state(self) -> AgentState:
        return self._state

    def update_model(self, model: str) -> None:
        self._state.model = model

    def update_reasoning(self, reasoning: Reasoning | None) -> None:
        self._state.reasoning = reasoning

    def replace_messages(self, messages: list[object]) -> None:
        self._state.messages = list(messages)

    def add_message(self, message: object) -> None:
        self._state.messages.append(message)

    async def run(self, prompt: str) -> None:
        stream = await self._stream_fn(prompt, self._state.model, self._state.reasoning)

        async for event in stream:
            await _dispatch_event(event)


async def _dispatch_event(event: object) -> None:
    match event:
        case ResponseCreatedEvent():
            await handle_response_created_event(event)
        case ResponseInProgressEvent():
            await handle_response_in_progress_event(event)
        case ResponseOutputItemAddedEvent():
            await handle_response_output_item_added_event(event)
        case _:
            return None


async def handle_response_created_event(event: ResponseCreatedEvent) -> None:
    del event


async def handle_response_in_progress_event(event: ResponseInProgressEvent) -> None:
    del event


async def handle_response_output_item_added_event(
    event: ResponseOutputItemAddedEvent,
) -> None:
    del event
