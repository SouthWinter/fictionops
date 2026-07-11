# API Agent Adapter

This directory defines the v1 platform-neutral contract for external AI agents that use FictionOps as a long-form writing harness.

The server is a thin local reference implementation, not a production hosted service. Closed-loop requests delegate to the public `fictionops.api` facade, which uses the same runtime as the CLI and Codex skill.

## Shape

- `openapi.yaml` defines the first HTTP surface.
- `server.py` provides a stdlib-only local thin server for smoke tests and adapter development.
- `schemas/` contains reusable JSON Schemas for goals, sessions, and staged outputs.
- `examples/` contains minimal request/response examples.

## Design Principles

- AI APIs are expected for normal use; no-model flows are only for smoke tests and recovery.
- The API should produce staged outputs, not silently mutate final manuscript files.
- Human-governed acceptance is the default decision mode.
- Provider credentials belong in deployment secrets, not in project files.

## Typical Flow

1. Create a session with a writing goal.
2. Ask the agent to write, revise, or audit a chapter.
3. Receive staged outputs plus metrics and review requirements.
4. Submit a human decision: accept, reject, or request revision.
5. Run FictionOps audits before applying or publishing.

## Local Smoke

From the `fictionops/` package directory:

```bash
python integrations/api-agent/server.py --host 127.0.0.1 --port 8765
```

Then post a request to `http://127.0.0.1:8765/v1/write-chapter`.

For the canonical runtime, send `runtime_mode: closed_loop`, `chapter_file`, and (for writing) `engine_file`. If `runner_command` is omitted, the workflow prepares a resumable run and stops before model execution. Legacy requests without `chapter_file` retain the v0 bundle behavior for compatibility.

The Python API is importable directly:

```python
from fictionops.api import write_chapter

report = write_chapter("chapter.md", engine_file="engine.md", runner=["python", "runner.py"])
```

The public facade and HTTP responses declare API version `1.0`. Additive response fields are allowed; removing or changing existing v1 fields requires a new API version.

Example runner command for a no-network smoke:

```json
"runner_command": ["python", "examples/agent_runner_echo.py"]
```

For real AI use, point `runner_command` at `examples/agent_runner_openai_chat.py` or another OpenAI-compatible runner configured with environment variables.
