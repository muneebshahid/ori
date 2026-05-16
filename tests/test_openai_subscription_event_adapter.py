"""Tests for normalizing subscription SSE payloads into canonical response events."""

import asyncio
import json
from collections.abc import AsyncIterator, Sequence

from ai.openai.response_events import ResponseEvent, ResponseEventType
from ai.openai.subscription_event_adapter import (
    SubscriptionEventPayload,
    normalize_subscription_events,
)


def test_normalize_subscription_events_maps_reasoning_message_and_done_payloads() -> (
    None
):
    """Map subscription SSE payloads into canonical response events."""

    events = _collect_events(
        [
            {
                "type": "response.created",
                "response": {"id": "resp_123"},
            },
            {
                "type": "response.output_item.added",
                "item": {
                    "id": "rs_123",
                    "type": "reasoning",
                    "summary": [],
                    "status": "in_progress",
                },
            },
            {
                "type": "response.reasoning_summary_text.delta",
                "item_id": "rs_123",
                "delta": "Exploring traces",
            },
            {
                "type": "response.output_item.done",
                "item": {
                    "id": "rs_123",
                    "type": "reasoning",
                    "summary": [
                        {"type": "summary_text", "text": "Exploring traces"},
                        {"type": "summary_text", "text": "Selecting an answer"},
                    ],
                    "status": "completed",
                },
            },
            {
                "type": "response.output_item.added",
                "item": {
                    "id": "msg_123",
                    "type": "message",
                    "status": "in_progress",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [],
                },
            },
            {
                "type": "response.content_part.added",
                "item_id": "msg_123",
                "part": {
                    "type": "output_text",
                    "text": "",
                    "annotations": [],
                },
            },
            {
                "type": "response.output_text.delta",
                "item_id": "msg_123",
                "delta": "Hello",
            },
            {
                "type": "response.output_item.done",
                "item": {
                    "id": "msg_123",
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Hello",
                            "annotations": [],
                        }
                    ],
                },
            },
            {
                "type": "response.done",
                "response": {
                    "id": "resp_123",
                    "status": "completed",
                    "output": [],
                },
            },
        ]
    )

    assert events == [
        {
            "type": ResponseEventType.CREATED,
            "response_id": "resp_123",
        },
        {
            "type": ResponseEventType.REASONING_ADDED,
            "item_id": "rs_123",
        },
        {
            "type": ResponseEventType.REASONING_DELTA,
            "delta": "Exploring traces",
        },
        {
            "type": ResponseEventType.REASONING_DONE,
            "item_id": "rs_123",
            "summary_text": "Exploring traces\n\nSelecting an answer",
            "reasoning_signature": json.dumps(
                {
                    "id": "rs_123",
                    "type": "reasoning",
                    "summary": [
                        {"type": "summary_text", "text": "Exploring traces"},
                        {"type": "summary_text", "text": "Selecting an answer"},
                    ],
                    "status": "completed",
                }
            ),
        },
        {
            "type": ResponseEventType.MESSAGE_ADDED,
            "item_id": "msg_123",
            "phase": "final_answer",
        },
        {
            "type": ResponseEventType.MESSAGE_TEXT_PART,
            "part_type": "output_text",
        },
        {
            "type": ResponseEventType.MESSAGE_TEXT_DELTA,
            "part_type": "output_text",
            "delta": "Hello",
        },
        {
            "type": ResponseEventType.MESSAGE_DONE,
            "item_id": "msg_123",
            "text": "Hello",
            "phase": "final_answer",
        },
        {
            "type": ResponseEventType.COMPLETED,
            "stop_reason": "stop",
        },
    ]


def test_normalize_subscription_events_maps_incomplete_tool_use_and_failures() -> None:
    """Normalize terminal subscription payload variants into canonical events."""

    events = _collect_events(
        [
            {
                "type": "response.completed",
                "response": {
                    "id": "resp_tool",
                    "status": "completed",
                    "output": [
                        {
                            "id": "call_123",
                            "type": "function_call",
                            "call_id": "call_123",
                            "name": "get_weather",
                            "arguments": '{"city":"Berlin"}',
                        }
                    ],
                },
            },
            {
                "type": "response.incomplete",
                "response": {
                    "id": "resp_incomplete",
                    "status": "incomplete",
                    "incomplete_details": {"reason": "content_filter"},
                },
            },
            {
                "type": "response.failed",
                "response": {
                    "id": "resp_failed",
                    "status": "failed",
                    "error": {"message": "Model overloaded"},
                },
            },
            {
                "type": "error",
                "message": "Socket closed",
            },
        ]
    )

    assert events == [
        {
            "type": ResponseEventType.COMPLETED,
            "stop_reason": "tool_use",
        },
        {
            "type": ResponseEventType.INCOMPLETE,
            "stop_reason": "error",
            "error_message": "OpenAI response was truncated by the content filter.",
        },
        {
            "type": ResponseEventType.FAILED,
            "message": "Model overloaded",
        },
        {
            "type": ResponseEventType.FAILED,
            "message": "Socket closed",
        },
    ]


def _collect_events(
    raw_events: Sequence[SubscriptionEventPayload],
) -> list[ResponseEvent]:
    async def _collect() -> list[ResponseEvent]:
        return [
            event
            async for event in normalize_subscription_events(_raw_stream(raw_events))
        ]

    return asyncio.run(_collect())


def _raw_stream(
    raw_events: Sequence[SubscriptionEventPayload],
) -> AsyncIterator[SubscriptionEventPayload]:
    async def _iterate() -> AsyncIterator[SubscriptionEventPayload]:
        for event in raw_events:
            yield event

    return _iterate()
