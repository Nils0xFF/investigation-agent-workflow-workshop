# Module 4 — Make it durable (35 min)

**Goal.** One investigation runs as a Mistral Workflow execution: started from Studio with a question, recorded step by
step, resumable after a crash, and returning the report. The agent runs as a durable worker of its own.

**Studio concepts.** `agents serve` (a durable local worker for the agent), the Mistral CLI (`mistral init`,
`mistral dev`, `mistral deploy`), Workflows (workflow, activity, worker, deployment), executions in Studio, idempotency
keys, the session view in Observability.

**You start from** module 3 and no `workflow/`: `mistral init workflow --preset workflow --no-git --yes` scaffolds it
(a worker app with hot reload, its own uv workspace and lockfile, a Dockerfile, and a skill that teaches your coding
agent the Workflows SDK). **You end with** `workflow/apps/worker/src/worker/workflows/investigate.py`, an execution
visible in **Studio → Workflows**, and `make check-4` passing.

## Why a workflow around an agent

An agent turn is minutes of tool calls. The thing that started it (a Slack message, a schedule, an alert) needs
something that survives a worker restart, retries what is safe to retry, records what happened, and can wait for a
person. That is a workflow. The agent stays an agent; the workflow owns the lifecycle.

## Requirements

- **R4.0 Scaffold.** `workflow/` is the project `mistral init --preset workflow` wrote: a uv workspace whose worker app
  lives in `apps/worker/`, with its entrypoints (`worker.py` discovers every workflow in the `worker.workflows` package
  and serves it; `dev.py` adds hot reload), `deploy/docker/Dockerfile.worker`, `mistral.json`, and the
  `capability-workflows` skill under `.agents/skills/`. Everything it generated stays. The one dependency to add is the
  Agents SDK, through the scaffold's wrapper: `cd workflow && bash tools/uv.sh add --package workflows-app
  "mistralai-agents==1.1.3"`.
- **R4.1 Models.** In `workflow/apps/worker/src/worker/workflows/investigate.py`: `InvestigateInput(question: str)`
  and `InvestigateResult(report: dict, text: str, session_id: str, tool_calls: list[str])`, plus
  `render_report(report: dict) -> str` that renders the report as plain text (summary, exception,
  `Where: <file> :: <symbol>`, confidence, root cause, evidence as `- [source] reference: proves` lines, next check)
  with no Markdown tables.
- **R4.2 Activity.** Same module: `agent_name()` (from `INVESTIGATION_AGENT_NAME`, default `investigation-agent`);
  `read_report(state) -> dict` that parses `Completed.text` as JSON when `stop_reason` is `None` and otherwise raises
  `RuntimeError` saying why (no final answer, failed turn with code and message, blocked on an approval, did not
  complete); `run_investigation(question, idempotency_key)`, an activity with `retry_policy_max_attempts=1` and a
  `start_to_close_timeout` longer than the turn timeout, that does `agents.Agent.load_from(agent_name=...)`,
  `start_session()`, `session.run(question, idempotency_key=..., timeout=...)`, returns
  `{"report", "session_id", "tool_calls"}` and cancels the session in a `finally`. `mistralai.agents` is imported
  inside the functions that use it: a module-level import of a network library fails the worker's determinism sandbox.
- **R4.3 Workflow.** Same module: a workflow named `investigate` with a display name and a description, whose
  entrypoint takes `InvestigateInput`, calls the activity with `workflows.get_execution_id()` as the idempotency key,
  and returns an `InvestigateResult` with the rendered text.
- **R4.4 Discovery.** Nothing registers the workflow by hand: `workflows.discover_all_workflows_in_package
  ("worker.workflows")` finds it, which is what the scaffold's `worker.py` entrypoint calls. The scaffold's Semgrep
  rules (`bash tools/uv.sh tool run semgrep@1.176.0 --config .agents/skills/capability-workflows/scripts/linting/rules
  --metrics=off apps/worker/src/worker/workflows`, from `workflow/`) report nothing.

## Definition of done

The coding agent's job ends at the first line; the rest you run yourself, from the cells after the prompt.

- `make check-4` passes.
- `sh scripts/workflow-env.sh` has copied `MISTRAL_API_KEY` and `INVESTIGATION_AGENT_NAME` into `workflow/.env`, next
  to the `DEPLOYMENT_NAME` the scaffold chose for you (`deployment-workflow-<you>`).
- Terminal 1: `make serve` (the agent, under your `INVESTIGATION_AGENT_NAME`). Terminal 2: `make worker`, which is
  `cd workflow && mistral dev` (the workflow worker, with hot reload). In **Studio → Workflows**, pick `investigate`,
  **Start Workflow** with
  `{"question": "Checkout is failing with KeyError: 'UK'. What's the root cause?"}`. The execution shows the activity,
  then completes with the report. **Observability** shows the agent session with every tool call.
- Kill the workflow worker mid-execution and start it again: the execution resumes from the activity.

## Studio clicks

- **Workflows → investigate → Start Workflow**: paste the input JSON, then open **Executions**.
- **Observability → Sessions** (or the link in the execution's result): the agent's trace.

## The prompt

The same text lives in `workshop/prompts/04-workflow.md`: `make vibe-4` opens Vibe with it already submitted, and `make fix-4` continues that session with the failing `make check-4` output appended. With another coding agent, paste it from the file:

```text
Build module 4 of this workshop: a durable workflow around one investigation.

Read AGENTS.md, docs/sdk-cheatsheet.md (the Workflows section), workshop/04-workflow.md, the scaffold's own skill at
workflow/.agents/skills/capability-workflows/SKILL.md, and every test in tests/m4/ first.

workflow/ was scaffolded with `mistral init --preset workflow`: keep everything it generated. Add the Agents SDK to the
worker package with `cd workflow && bash tools/uv.sh add --package workflows-app "mistralai-agents==1.1.3"` (the same
version agent/ pins), then create one module, workflow/apps/worker/src/worker/workflows/investigate.py, holding the
models, the activity and the workflow, so that R4.0 to R4.4 hold and `make check-4` passes. The worker discovers the
workflow by convention; do not edit the entrypoints.

The activity is the only place that talks to the agent; the workflow only orchestrates. The activity must not be
retried (a retry would start a second investigation): the execution ID is the idempotency key instead. Import
mistralai.agents inside the functions that use it, never at module level: workflow modules run in a determinism
sandbox that rejects network libraries at import time. Keep the workflow independent of agent/: it consumes the report
as JSON. Do not edit tests/.
```

## The loop

1. `mistral init workflow --preset workflow --no-git --yes`, read what it wrote, `sh scripts/workflow-env.sh`.
2. Prompt, build, `make check-4` until it passes.
3. `make serve`, `make worker`, start an execution in Studio. Read the execution's timeline.
4. Break it on purpose: stop the agent worker, start an execution, watch the activity fail with the message your
   `read_report` wrote. Restart the agent worker, start again.
5. Commit.

## Checkpoint

`git diff module-4 -- workflow`.

## Watch out for

- `agents serve` and the workflow worker both need **workflows enabled on your API key** (the key's workspace must have
  Workflows). The workflow's `DEPLOYMENT_NAME` lives in `workflow/.env`, where the scaffold put it; the agent worker
  reads the root `.env`, which has none, so the two never share a queue.
- `mistral init` needs the CLI signed in first (the `setup-cli` cell: `mistral login --api-key -` fed from `.env`;
  device-code sign-in is not available yet), and Bun on the
  machine; the CLI installer offers it.
- The scaffold's `.python-version` says 3.14: the first `mistral dev` downloads it through uv. Nothing of yours runs on
  it except the worker.
- Give the agent a name that is yours (`-ada`); a room full of `investigation-agent` workers would all claim each
  other's sessions. The deployment name is already yours: the scaffold derived it from your login.
- Never run `make worker` on a deployment name that a managed deployment also serves: both would take executions.
