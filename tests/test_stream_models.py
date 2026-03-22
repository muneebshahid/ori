from ai.types.stream import (
    AssistantMessage,
    ToolCallDeltaEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)


def test_tool_call_stream_events_preserve_partial_message() -> None:
    partial = AssistantMessage()

    start_event = ToolCallStartEvent(type="tool_call_start", partial=partial)
    delta_event = ToolCallDeltaEvent(
        type="tool_call_delta",
        delta='{"directory":"."}',
        partial=partial,
    )
    end_event = ToolCallEndEvent(type="tool_call_end", partial=partial)

    assert start_event.partial is partial
    assert delta_event.delta == '{"directory":"."}'
    assert end_event.partial is partial
