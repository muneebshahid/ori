"""Example local runner for one headless piy prompt."""

import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from agent.agent import Agent
from agent.tools import build_tools
from agent.types import AgentEvent
from ai.openai.provider import stream_api
from settings import settings


def main() -> None:
    """Run the example local runner."""

    raise SystemExit(asyncio.run(run_cli(sys.argv[1:])))


async def run_cli(argv: Sequence[str]) -> int:
    """Run a prompt from command arguments or standard input."""

    prompt = _read_prompt(argv, sys.stdin)
    if not prompt:
        print("Provide a prompt as arguments or stdin.", file=sys.stderr)
        return 2

    await run_prompt(prompt)
    return 0


async def run_prompt(
    prompt: str,
    *,
    agent: Agent | None = None,
    output: TextIO | None = None,
) -> None:
    """Run one prompt through an agent and write JSON event lines."""

    active_agent = agent or create_agent()
    event_output = output or sys.stdout
    active_agent.add_user_message(prompt)

    async for event in active_agent.run():
        event_output.write(_serialize_event(event))
        event_output.write("\n")


def create_agent(cwd: Path | str | None = None) -> Agent:
    """Create the default local agent backed by OpenAI and built-in tools."""

    working_directory = _resolve_cwd(cwd)
    return Agent(
        stream_fn=stream_api,
        model=settings.openai_model,
        tools=build_tools(working_directory),
        cwd=working_directory,
    )


def _read_prompt(argv: Sequence[str], stdin: TextIO) -> str:
    """Read a prompt from positional arguments or standard input."""

    if argv:
        return " ".join(argv).strip()
    return stdin.read().strip()


def _resolve_cwd(cwd: Path | str | None) -> Path:
    """Resolve the local working directory for tools and instructions."""

    if cwd is None:
        return Path.cwd().resolve()
    return Path(cwd).expanduser().resolve()


def _serialize_event(event: AgentEvent) -> str:
    """Serialize one agent event for line-oriented local output."""

    return event.model_dump_json()


if __name__ == "__main__":
    main()
