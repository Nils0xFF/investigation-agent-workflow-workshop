# Building Production-Ready Agentic Workflows

Build an engineering investigation agent on Mistral Studio, with prompts rather than copy-paste. You ask
it *"What's causing the KeyError in checkout?"*; it reads the error in Sentry, opens the code on GitHub, and answers with
a structured report that names the file, the function, the root cause and the evidence. Then you make it durable with
a Workflow.

The workshop's method is the product: every module is a **requirements card** you hand to your coding agent, with
**acceptance tests** that say when it is done. The agent you build gets the same treatment: its `instructions.md` is a
requirements document, and an **eval loop** over six planted bugs says whether the requirements are good enough.

```
question ──> investigate workflow ──> agent session ──> Sentry connector (read-only)
                 (durable)             (Agents SDK)   └─> GitHub connector (read-only)
                                            │
                                            └──> InvestigationReport (structured output) ──> evals: score + judge + gate
```

Everything runs on free tiers: Mistral Studio, Sentry Developer, GitHub Free. Nothing needs a credit card.

## Modules

| # | Module | You build | Done when |
|---|---|---|---|
| 0 | [Pre-work](workshop/00-prework.md) | accounts, tools, six errors in Sentry | `uv run pytest tests/test_sample_app.py` passes |
| 1 | [A testable agent](workshop/01-agent-skeleton.md) | `agent/main.py`, `instructions.md`, `report.py`, `investigate.py`, `ask.py` | `make check-1` |
| 2 | [Eyes, with guardrails](workshop/02-connectors-and-policy.md) | Sentry + GitHub connectors, deny-by-default policy, audit hook, two skills | `make check-2` |
| 3 | [The eval loop](workshop/03-eval-loop.md) | `evals/`: scorers, judge, runner, gate; then iterate on the instructions | `make check-3` and `make eval` passes the gate |
| 4 | [Make it durable](workshop/04-workflow.md) | `workflow/` from `mistral init`, then the `investigate` workflow, run from Studio | `make check-4` and an execution in Studio |
| 5 | [Stretch](workshop/05-stretch.md) | `agents deploy`, `mistral deploy`, a Slack trigger, a schedule | the agent answers in Slack |

`main` is the starter you build on, and it contains **no agent code**: there is no `agent/` yet (module 1 scaffolds it
with `agents init`), no `workflow/` (module 4 scaffolds it with `mistral init`), and `evals/` holds only the six cases. The cards, the prompts and the acceptance tests in `tests/` are the specification;
your coding agent writes the code against them. You work in your own fork (the GitHub connector reads the sample app
from it), committing and pushing at the end of each module. The reference solution lives on the `solution` branch, one
commit per module, tagged `module-1` .. `module-4`: `git diff module-2 -- agent` shows how your build differs from the
reference, and `git checkout module-2 -- agent` catches you up if you fall behind.

## Where to work

**[`WORKSHOP.md`](WORKSHOP.md) is the workshop.** Every command and every prompt is a cell with a ▶ button: run it
where it sits, read the output under it, copy it if you prefer. Pick one way to open it:

1. **VS Code on your machine (preferred)** with the
   [Runme](https://marketplace.visualstudio.com/items?itemName=stateful.runme) extension (VS Code offers it when you
   open the folder): fork, clone, open `WORKSHOP.md`. Its section 0.2 installs the three tools the day needs (uv, Vibe,
   the Mistral CLI), one cell each. The workspace settings send the Vibe cells to the full terminal panel rather than
   the small notebook terminal.
2. **GitHub Codespaces (fallback, nothing to install)**: on your fork, *Code → Codespaces → Create codespace*. The
   container runs the same three installs plus the dependencies, opens `WORKSHOP.md` as a notebook, and reads your
   `MISTRAL_API_KEY`, `SENTRY_CONNECTOR_NAME`, `GITHUB_CONNECTOR_NAME` and `SENTRY_DSN` from Codespaces secrets into
   `.env` if you set them first (*Settings → Codespaces → Secrets*). It is a remote machine: slower to start, and Vibe
   runs in the browser's terminal.
3. **A plain terminal**, with either of the above: every cell is also a `make` target. `make vibe-1`, `make check-1`,
   `make fix-1` (only while `check-1` reports failures), … in that order, with `WORKSHOP.md` open beside you for the words.

```sh
sh scripts/bootstrap-env.sh  # .env from the example, filled from the environment where possible; then complete it
make setup
make send-error N=all        # six errors land in your Sentry project
make check-1                 # fails until module 1 is built
```

## Layout

| Path | What it is |
|---|---|
| `agent/` | The Agents SDK project, created by `agents init` in module 1: the agent, its instructions, report model, connectors, policy, hooks, skills |
| `evals/` | The eval loop: dataset, scorers, LLM judge, runner, gate |
| `workflow/` | The Mistral CLI workflow project, created by `mistral init` in module 4: one durable execution per investigation |
| `sample-app/` | A shop with six planted bugs and the script that sends them to Sentry |
| `tests/` | Acceptance tests per module |
| `WORKSHOP.md` | The runnable path through the workshop: one ▶ cell per command and prompt |
| `workshop/` | Requirements cards, the prompt files, Studio click paths, facilitator notes |
| `.devcontainer/` | The Codespaces / Dev Container definition: uv, Vibe, dependencies, Runme |
| `docs/sdk-cheatsheet.md` | The exact SDK API this repository uses, for you and your coding agent |

## Commands

See the comments in the [Makefile](Makefile): `check-N`, `test`, `lint`, `info`, `chat`, `ask`, `serve`, `eval`,
`send-error`, `worker`; `vibe-N` and `fix-N` hand a module's prompt (or its failing tests) to Vibe. `make present`
opens an optional terminal-slides version of the same content (`workshop/present/deck.md`, needs presenterm) for a
facilitator who prefers to present from a terminal.
