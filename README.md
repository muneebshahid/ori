# piy

> ⚠️ **Work in Progress** — This project is under active development and APIs may change.

A minimal, headless harness for building tool-using AI agents in Python.

## Overview

**piy** is a headless agent kernel for building intelligent AI agents in Python. Providers, tools, events, and serialization are explicit runtime contracts. Start minimal and compose the agent loop you need without adopting a terminal UI or application framework.

## Features

- **Headless Runtime**: Run agents from Python code or a small local command without a UI dependency
- **Explicit Contracts**: Swap providers, tools, event handlers, and serializers without modifying core agent logic
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
└── tests/           # Test suite
```

## Quick Start

Run a local prompt:

```bash
uv run python -m examples.local_runner "Inspect the current repository"
```

Or pipe a prompt through stdin:

```bash
printf "Inspect the current repository" | uv run python -m examples.local_runner
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
