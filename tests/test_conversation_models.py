from ai.types.conversation import AssistantTurn, UserMessage
from ai.types.stream import (
    ReasoningBlock,
    TextBlock,
    ToolCallBlock,
)


def test_user_message_defaults_role() -> None:
    message = UserMessage(content="hello")

    assert message.role == "user"
    assert message.content == "hello"


def test_assistant_turn_preserves_replay_metadata() -> None:
    turn = AssistantTurn(
        response_id="resp_123",
        content=[
            ReasoningBlock(
                summary_text="Plan the answer",
                reasoning_id="rs_123",
                encrypted_content="enc_123",
            ),
            TextBlock(
                text="final answer",
                message_id="msg_123",
                phase="final_answer",
            ),
        ],
    )

    assert turn.role == "assistant"
    assert turn.status == "completed"
    assert turn.response_id == "resp_123"

    reasoning_block = turn.content[0]
    assert isinstance(reasoning_block, ReasoningBlock)
    assert reasoning_block.summary_text == "Plan the answer"
    assert reasoning_block.reasoning_id == "rs_123"
    assert reasoning_block.encrypted_content == "enc_123"

    text_block = turn.content[1]
    assert isinstance(text_block, TextBlock)
    assert text_block.text == "final answer"
    assert text_block.message_id == "msg_123"
    assert text_block.phase == "final_answer"


def test_assistant_turn_supports_non_completed_status() -> None:
    turn = AssistantTurn(
        status="error",
        error_message="request failed",
    )

    assert turn.status == "error"
    assert turn.error_message == "request failed"
    assert turn.content == []


def test_assistant_turn_supports_tool_call_blocks() -> None:
    turn = AssistantTurn(
        content=[
            ToolCallBlock(
                call_id="call_123",
                name="ls",
                arguments={"directory": "."},
                provider_item_id="fc_123",
            )
        ]
    )

    block = turn.content[0]
    assert isinstance(block, ToolCallBlock)
    assert block.call_id == "call_123"
    assert block.name == "ls"
    assert block.arguments == {"directory": "."}
    assert block.provider_item_id == "fc_123"
