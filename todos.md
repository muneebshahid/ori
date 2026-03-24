Remaining tool-call and server-streaming work

Replay serialization
- Serialize prior assistant tool calls from `ToolCallBlock` to OpenAI function-call input items in `ai/openai/serialization.py`.
- Serialize `ToolResultTurn` to OpenAI function-call output items in `ai/openai/serialization.py`.
- Extend `serialize_history_items()` to replay completed assistant turns that contain text, reasoning, and tool-call blocks.
- Add serialization tests for replaying assistant tool calls and `ToolResultTurn`.

Agent runtime
- Extend the agent runtime to accept `tools` and thread them into provider calls.
- Change the agent from an internal sink-only runner to an async producer of `AgentEvent`s.
- Keep `StreamEvent` as the normalized single-response stream and use `AgentEvent` for whole-run lifecycle.
- Emit agent-level lifecycle events for:
  - run start/end
  - turn start/end
  - message start/update/end
  - tool execution start/update/end
- Keep tool-call stream handling internal to the agent loop.
- Keep `_build_assistant_turn()` preserving tool-call blocks so assistant turns can be replayed after a tool-use stop.

Tool execution
- Add a minimal tool registry or dispatch mapping in the agent layer.
- On completed tool-call blocks, execute tools internally and append `ToolResultTurn` to history.
- Continue the loop until the assistant stops without requesting more tool use.
- Implement the first concrete tool and its schema only after provider plumbing and replay are in place.

Server mode
- Treat the server as the single execution locus for tools, filesystem access, and model interaction.
- Add a session/thread-scoped subscription manager for connected clients.
- Add bounded per-connection outgoing queues so slow clients do not block fast ones.
- Keep live event delivery separate from persisted conversation history.
- Support atomic "resume history + subscribe for live updates" behavior so reconnecting clients do not miss in-flight turn state.
- Decide and enforce thread control rules:
  - one active controller per thread
  - additional clients are observers unless explicitly granted control

Tests
- Add agent tests for tool-use loops and history updates.
- Add tests for emitted `AgentEvent` ordering across:
  - plain assistant response
  - assistant response with tool use
  - tool failure
  - interrupted or aborted turn
- Add server-mode tests for:
  - multi-client subscription fan-out
  - slow subscriber isolation
  - unsubscribe cleanup
  - resume plus live subscription ordering

Important shape constraints
- `ToolResultTurn.call_id` must exactly match the `call_id` on the corresponding assistant `ToolCallBlock`.
- Do not introduce a combined tool turn that stores both call and result together.
- Keep the history shape as:
  - `UserMessage`
  - `AssistantTurn` with text, reasoning, and tool-call blocks
  - `ToolResultTurn`
- Keep agent execution server-side; clients are transport/control surfaces, not execution hosts.
