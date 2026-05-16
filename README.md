# piy

> ⚠️ **Work in Progress** — This project is under active development and APIs may change.

A minimal, highly extensible harness for building AI agents in Python. Inspired by [pi.dev](https://pi.dev) (TypeScript).

## Overview

**piy** is a plugin-first harness for building intelligent AI agents in Python. Everything is pluggable—providers, tools, event handlers, and serialization can be swapped or extended without touching core logic. Start minimal and compose your agent exactly as needed.

## Features

- **Plugin Architecture**: Swap providers, tools, event handlers, and serializers without modifying core agent logic
- **Minimal Core**: Only what you need—everything else is optional
- **Async First**: Built on Python async/await for non-blocking I/O
- **Type Safe**: Full Pydantic integration with mypy support
- **Streaming Support**: Real-time event streaming via plugin-based event dispatch
- **Tool Execution**: Pluggable tool definitions and execution strategies
- **Reasoning**: Extensible support for extended thinking workflows

## Architecture

```
piy/
├── agent/           # Core agent orchestration and event dispatch
├── ai/
│   ├── openai/      # OpenAI provider implementation
│   └── types/       # Shared type definitions for contracts, tools, and streams
├── ui/              # User interface layer
└── tests/           # Test suite
```

## Quick Start

```python
# Create and run an agent
from agent.agent import Agent

agent = Agent()
# Stream events from the agent
async for event in agent.run(...):
    # Handle events as they arrive
    pass
```

## Development

Install dependencies:
```bash
uv sync
```

Run tests:
```bash
make test
```

Format and type-check:
```bash
make format
make type_check
```
