from collections.abc import AsyncIterator, Sequence
from typing import TYPE_CHECKING, Literal, cast

from openai import AsyncOpenAI
from openai.types.responses import (
    ResponseCompletedEvent,
    ResponseContentPartAddedEvent,
    ResponseCreatedEvent,
    ResponseFailedEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseReasoningSummaryPartDoneEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseRefusalDeltaEvent,
    ResponseTextDeltaEvent,
)
from openai.types.responses.response_output_message import (
    Content as ResponseMessageContent,
)
from openai.types.responses.response_reasoning_item import (
    Summary as ResponseReasoningSummary,
)

from ai.openai_client import create_openai_client
from ai.contracts import AsyncEventStream, Reasoning as AppReasoning
from ai.types import (
    AssistantMessage,
    ReasoningBlock,
    ReasoningDeltaEvent,
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

if TYPE_CHECKING:
    from openai.types.shared_params.reasoning import Reasoning as OpenAIReasoning


async def stream(
    prompt: str,
    model: str,
    reasoning: AppReasoning | None = None,
    *,
    client: AsyncOpenAI | None = None,
) -> AsyncEventStream:
    """Stream internal assistant events from the OpenAI Responses API."""

    active_client = client or create_openai_client()
    raw_stream = await active_client.responses.create(
        model=model,
        input=prompt,
        stream=True,
        reasoning=cast("OpenAIReasoning | None", reasoning),
    )
    return _adapt_stream(raw_stream)


async def _adapt_stream(
    raw_stream: AsyncIterator[object],
) -> AsyncIterator[StreamEvent]:
    partial = AssistantMessage()
    current_reasoning_block: ReasoningBlock | None = None
    current_text_block: TextBlock | None = None
    current_text_content_part: Literal["output_text", "refusal"] | None = None

    yield StreamStartEvent(type="start", partial=partial)

    async for event in raw_stream:
        match event:
            # Start of a new response
            case ResponseCreatedEvent():
                partial.response_id = event.response.id

            # Reasoning block started
            case ResponseOutputItemAddedEvent() if event.item.type == "reasoning":
                current_reasoning_block = ReasoningBlock(
                    type="reasoning",
                    reasoning="",
                    reasoning_id=event.item.id,
                )
                current_text_block = None
                current_text_content_part = None
                partial.content.append(current_reasoning_block)
                yield ReasoningStartEvent(
                    type="reasoning_start",
                    partial=partial,
                )

            # Reasoning summary block text delta
            case ResponseReasoningSummaryTextDeltaEvent() if (
                current_reasoning_block is not None
            ):
                current_reasoning_block.reasoning += event.delta
                yield ReasoningDeltaEvent(
                    type="reasoning_delta",
                    delta=event.delta,
                    partial=partial,
                )

            # Separate summary parts with a blank line while streaming.
            case ResponseReasoningSummaryPartDoneEvent() if (
                current_reasoning_block is not None
            ):
                current_reasoning_block.reasoning += "\n\n"
                yield ReasoningDeltaEvent(
                    type="reasoning_delta",
                    delta="\n\n",
                    partial=partial,
                )

            # Reasoning block finalized with the canonical item shape.
            case ResponseOutputItemDoneEvent() if (
                event.item.type == "reasoning" and current_reasoning_block is not None
            ):
                if summary_text := _join_reasoning_summary_text(event.item.summary):
                    current_reasoning_block.reasoning = summary_text

                yield ReasoningEndEvent(
                    type="reasoning_end",
                    partial=partial,
                )
                current_reasoning_block = None

            # Text block started
            case ResponseOutputItemAddedEvent() if event.item.type == "message":
                current_text_block = TextBlock(type="text", text="")
                current_reasoning_block = None
                current_text_content_part = None
                partial.content.append(current_text_block)
                yield TextStartEvent(
                    type="text_start",
                    partial=partial,
                )

            # Track the active visible content part for message output.
            case ResponseContentPartAddedEvent() if current_text_block is not None:
                match event.part.type:
                    case "output_text":
                        current_text_content_part = "output_text"
                    case "refusal":
                        current_text_content_part = "refusal"
                    case _:
                        current_text_content_part = None

            # Text and refusal deltas are surfaced through the same text block stream.
            case ResponseTextDeltaEvent() | ResponseRefusalDeltaEvent() if (
                current_text_block is not None
                and current_text_content_part in {"output_text", "refusal"}
            ):
                current_text_block.text += event.delta
                yield TextDeltaEvent(
                    type="text_delta",
                    delta=event.delta,
                    partial=partial,
                )

            # Message blocks are finalized from the canonical completed item.
            case ResponseOutputItemDoneEvent() if (
                event.item.type == "message" and current_text_block is not None
            ):
                current_text_block.text = _join_message_text(event.item.content)
                yield TextEndEvent(
                    type="text_end",
                    partial=partial,
                )
                current_text_block = None
                current_text_content_part = None

            # Response completed successfully
            case ResponseCompletedEvent():
                yield StreamDoneEvent(
                    type="done",
                    message=partial.model_copy(deep=True),
                )
                return

            # Response failed
            case ResponseFailedEvent():
                yield StreamErrorEvent(
                    type="error",
                    message=_extract_error_message(event),
                    partial=partial.model_copy(deep=True),
                )
                return


def _extract_error_message(event: ResponseFailedEvent) -> str:
    error = getattr(event.response, "error", None)
    if error is None:
        return "OpenAI response failed."

    message = getattr(error, "message", None)
    if isinstance(message, str) and message:
        return message

    return "OpenAI response failed."


def _join_reasoning_summary_text(
    summary: Sequence[ResponseReasoningSummary],
) -> str:
    return "\n\n".join(item.text for item in summary if item.text)


def _join_message_text(content: Sequence[ResponseMessageContent]) -> str:
    parts = []
    for item in content:
        if item.type == "output_text":
            parts.append(item.text)
        elif item.type == "refusal":
            parts.append(item.refusal)
    return "".join(parts)
