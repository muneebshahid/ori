from openai import AsyncOpenAI

from ai.openai_client import create_openai_client
from ai.contracts import AsyncEventStream


async def stream(
    prompt: str,
    model: str,
    *,
    client: AsyncOpenAI | None = None,
) -> AsyncEventStream:
    """Stream OpenAI Responses API events for a prompt."""

    active_client = client or create_openai_client()
    return await active_client.responses.create(
        model=model,
        input=prompt,
        stream=True,
    )
