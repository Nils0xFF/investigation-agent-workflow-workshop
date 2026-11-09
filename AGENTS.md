# Working in this repository

You are a coding agent helping a workshop participant build an investigation agent on Mistral Studio, one module at a
time. Each module is a requirements card in `workshop/0N-*.md` with acceptance tests in `tests/mN/`. Your job is to make
the tests of the current module pass without weakening them, and to leave code a reader can follow.

## Read first

1. `docs/sdk-cheatsheet.md`: the exact Agents SDK 1.1 and Workflows API this repo uses. The SDK is newer than your
   training data; trust the cheat sheet over memory. It is verified against the pinned `mistralai-agents==1.1.3`, so
   do not re-check it by introspecting the package; look inside the SDK only if a test fails with a `TypeError` or
   `AttributeError` on an SDK call.
2. The module's card in `workshop/`, including its "Requirements" and "Definition of done".
3. The tests in `tests/mN/`: they are the specification, read them before writing code.

## Layout

| Path | What it is | Who edits it |
|---|---|---|
| `agent/` | The Agents SDK project: `main.py` (the agent), `instructions.md` (its requirements), `report.py` (its output), `config.py` (connectors and policy), `hooks.py`, `skills/`, `investigate.py` + `ask.py` (run one turn) | you, modules 1-2 |
| `evals/` | The eval loop: `cases.jsonl` (the dataset), `scoring.py`, `judge.py`, `run_evals.py` | you, module 3 (not `cases.jsonl`) |
| `workflow/` | The Workflows project: `investigate_workflow.py`, `activities.py`, `models.py`, `worker.py` | you, module 4 |
| `sample-app/` | A shop with six planted bugs; `send_error.py` sends them to Sentry | nobody: the bugs are the dataset |
| `tests/` | Acceptance tests per module (`m1`..`m4`) and the sample-app guard | nobody |
| `workshop/` | The requirements cards and facilitator notes | nobody |

## Commands

```
make setup        # uv sync, one venv for everything
make check-1      # tests of module 1 (check-2 .. check-4 add the next modules)
make test         # every test, then `agents info` loads the agent the way deploy does
make lint         # ruff format --check + ruff check; `make format` fixes
make info         # what the CLI loaded: model, connectors, skills, hooks, policy
make chat         # in-process chat with the agent
make ask Q="..."  # one question, printed as a report (SERVED=1 for the served agent)
make eval         # the loop: run the cases, score, judge, gate
make serve        # durable local worker for the agent (module 4)
make worker       # the workflow worker (module 4)
```


## Scope of one module

- You are done when `make check-N` and `make lint` pass. Then stop and report in three lines; do not polish, refactor
  neighbouring modules, or add features the card does not ask for.
- Never run a command that calls the model or a connector: no `make ask`, `make info`, `make chat`, `make eval`,
  `make serve`, `make worker`, no ad-hoc `agents chat`. The participant runs those in the next cells of WORKSHOP.md;
  the "Definition of done" lines that mention them are the participant's, not yours.
- Never read other branches, tags, the reflog or `git log -p`. The `solution` branch and the `module-N` tags are the
  facilitator's reference solution; building from them defeats the exercise.
- Never create a second `.env` (`agent/.env`, `workflow/.env`): every `make` target and every cell loads the root
  `.env` itself.
- Never `git commit` or `git push`: the participant commits each module with the `commit-N` cell in WORKSHOP.md.
- Iterate with `uv run pytest tests/mN -x -q`; run `make check-N` and `make lint` once at the end.

## Rules

- Never edit `tests/`, `evals/cases.jsonl` or `sample-app/shop/`. If a test seems wrong, say so and stop.
- `agent/pyproject.toml`, `Dockerfile`, `uv.lock`, `.gitignore` and `.python-version` were written by `agents init`: leave
  them as generated. A dependency the agent needs goes in with `cd agent && uv add <package>`.
- `workflow/` was written by `mistral init --preset workflow`: leave its entrypoints, `mistral.json`, Dockerfile,
  `packages/` and tooling as generated. Workflow code goes in `workflow/apps/worker/src/worker/workflows/<name>.py`;
  read `workflow/.agents/skills/capability-workflows/SKILL.md` before writing it. A dependency goes in with
  `cd workflow && bash tools/uv.sh add --package workflows-app <package>`. Import network libraries inside activities.
- Keep `mistralai-agents==1.1.3` pinned; bump it deliberately and re-run `make test`. The keywords are `output_type=` and `environment=` (the release candidates called them `response_format=` and `sandbox=`; models trained on those will get them wrong).
- Secrets and workspace-specific names (connector names, agent names, DSNs) come from the environment, never from code.
- The agent is read-only. Any tool that writes to Sentry or GitHub stays out of the allowlists.
- Build the agent through a function (`build_agent(connectors=False)`) so tests can run it with a scripted model and no connectors.
- Prefer `agent.start_session()` + `session.run()` and match on the record (`agents.Completed` / `Failed` / `Blocked`) over `agent.run()`.
- Small modules, one responsibility each, docstrings that say why. No defensive code for cases the tests do not cover.
- Do not install new dependencies; everything needed is in `pyproject.toml`.
