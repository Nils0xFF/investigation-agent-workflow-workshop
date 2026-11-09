# Module 1 — A testable agent (30 min)

**Goal.** An agent that answers an investigation question with a validated `InvestigationReport`, built so a test can
drive it with a scripted model and no network.

**Studio concepts.** The Agents SDK `Agent` (model + instructions + what it can use), structured output
(`output_type`), sessions and turn records, `agents.testing.ScriptedModel`, the `agents` CLI (`info`, `chat`).

**You start from** no `agent/` at all: `uv run agents init agent --no-git` scaffolds it (project file, Dockerfile,
lockfile, a hello-world `main.py`). **You end with** `agent/main.py`, `instructions.md`, `report.py`, `investigate.py`,
`ask.py`, and `make check-1` passing.

## Why this first

Everything later (connectors, evals, the workflow) consumes the report. Nailing the output contract first means every
later module is testable, and it forces the key habit: the instructions are a requirements document for the model,
and the report model is its acceptance test.

## Requirements

- **R1.0 Scaffold.** `agent/` is the project `agents init` wrote. Its `pyproject.toml`, `Dockerfile`, `uv.lock`,
  `.gitignore` and `.python-version` stay as generated; `main.py` is replaced. A dependency the agent needs goes in with
  `cd agent && uv add <package>`, never by rewriting the project file.
- **R1.1 Report.** `agent/report.py` defines `InvestigationReport` (Pydantic) with: `summary: str`, `exception: str | None`,
  `file: str | None`, `symbol: str | None`, `root_cause: str`, `confidence: Literal["low","medium","high"]`,
  `evidence: list[Evidence]` where `Evidence` has `source: Literal["sentry","github","other"]`, `reference: str`,
  `proves: str`, and `next_check: str | None`. Every field has a `Field(description=...)` the model will read.
- **R1.2 Instructions.** `agent/instructions.md` has `[ROLE]`, `[READ-ONLY]`, `[INVESTIGATION]` and `[REPORT]` sections.
  `[REPORT]` explains every report field by name in backticks. `[INVESTIGATION]` is the procedure: find the error, read
  a representative event, open the responsible code at the recorded release, explain the defect as a fact about the
  code. (Module 2 adds the line that tells the model which skill to load.)
- **R1.3 Agent.** `agent/main.py` exposes `build_agent(*, connectors: bool = True, name: str | None = None) -> agents.Agent`
  and a module-level `agent = build_agent()`. Model `mistral-large-4`, `output_type=InvestigationReport`,
  `max_iterations` at most 40, a low temperature, `instructions` read from `instructions.md` next to the file. The
  name is `INVESTIGATION_AGENT_NAME` from the environment, else `investigation-agent`. The `connectors` flag has no
  effect yet; module 2 gives it one.
- **R1.4 One turn as data.** `agent/investigate.py` exposes `investigate(question, *, agent, timeout=600) -> Investigation`.
  It opens `agent.start_session()`, runs `session.run(question, output_type=InvestigationReport, timeout=timeout)`,
  reads the record into an `Investigation` dataclass (`question`, `session_id`, `report`, `text`, `tool_calls`, `error`,
  and an `ok` property) and cancels the session in a `finally`. An answer that is not a valid report, a failed turn, a
  blocked turn and a turn without a final answer all become `report=None` with a sentence in `error`; nothing raises.
  `served_agent(name=None)` returns `agents.Agent.load_from(agent_name=...)` for the agent `agents serve` runs.
- **R1.5 Terminal.** `agent/ask.py` asks one question (`--served` for the served agent, `--json` for the raw report) and
  prints the report readably: the summary, exception, file and symbol, confidence, root cause, evidence, next check,
  and the tool calls the turn made.

## Definition of done

The coding agent's job ends at the first line; the rest you run yourself, from the cells after the prompt.

- `make check-1` passes (the tests in `tests/m1/` are the specification; read them).
- `make info` prints the agent with model, instructions and no tools.
- Live: `make ask Q="What's causing the latest ValueError in Sentry?"` prints a report. Without connectors the model
  cannot look at anything, so expect low confidence and a `next_check`; that is correct behaviour, and it is the baseline
  module 2 improves on.

## The prompt

The same text lives in `workshop/prompts/01-agent-skeleton.md`: `make vibe-1` opens Vibe with it already submitted, and `make fix-1` continues that session with the failing `make check-1` output appended. With another coding agent, paste it from the file:

```text
Build module 1 of this workshop: a testable investigation agent.

Read AGENTS.md, docs/sdk-cheatsheet.md, workshop/01-agent-skeleton.md and every test in tests/m1/ before writing code.
agent/ was scaffolded with `agents init`: keep its pyproject.toml, Dockerfile, uv.lock, .gitignore and .python-version
as they are, replace the hello-world main.py, and create agent/report.py, agent/instructions.md, agent/investigate.py
and agent/ask.py so that the requirements R1.0 to R1.5 in the card hold and `make check-1` passes.

Constraints: use the API exactly as the cheat sheet shows it (mistralai-agents 1.1: `output_type=`, start_session() +
session.run(), match on agents.Completed / Failed / Blocked). Do not edit tests/. When a test fails, read the test and
fix the implementation. Write the instructions as a requirements document for the model: short sections, one rule per
line, every report field explained.
```

## The loop

1. Paste the prompt. Let the agent read and build.
2. Run `make check-1`. Paste any failure back verbatim: *"`make check-1` fails with: `<output>`. Fix the implementation,
   not the test."* Repeat until it passes. Two or three rounds is normal.
3. Run `make info`, then the live `make ask`. Read the report the model produced: does the instructions file say what
   you meant? Change a sentence, ask again.
4. Commit: `git commit -am "Module 1: a testable agent"`.

## Checkpoint

The reference solution is tagged `module-1`. Compare with `git diff module-1 -- agent`. Behind schedule?
`git checkout module-1 -- agent` and carry on.

## Watch out for

- The SDK's CLI imports `main:agent` at module scope, so `main.py` must not run anything at import time.
- `output_type` makes every answer JSON, including in `agents chat`. That is the point: the report is data.
- `Completed.output` is `None` when the turn stopped early (`stop_reason="iteration_limit"`); an answer that is not valid
  JSON is `agents.InvalidOutput`. Both are errors in `Investigation`, not exceptions.
