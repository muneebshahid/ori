from typing import TYPE_CHECKING, cast

from openai import AsyncOpenAI

from ai.openai_client import create_openai_client
from ai.contracts import AsyncEventStream, Reasoning as AppReasoning

if TYPE_CHECKING:
    from openai.types.shared_params.reasoning import Reasoning as OpenAIReasoning


async def stream(
    prompt: str,
    model: str,
    reasoning: AppReasoning | None = None,
    *,
    client: AsyncOpenAI | None = None,
) -> AsyncEventStream:
    """Stream OpenAI Responses API events for a prompt."""

    active_client = client or create_openai_client()
    return await active_client.responses.create(
        model=model,
        input=prompt,
        stream=True,
        reasoning=cast("OpenAIReasoning | None", reasoning),
    )
