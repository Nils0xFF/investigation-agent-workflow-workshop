# Module 0 — Pre-work (do this before the workshop, ~40 minutes)

The workshop is building. Account setup is not building, so it happens before you arrive. The steps live in
**section 0 of [`WORKSHOP.md`](../WORKSHOP.md)**, the same file you will work from on the day, with the *what* and
*why* of each one. This page is the checklist. If a step fails, bring the error: the first 15 minutes of the workshop
are a setup clinic.

## Checklist

| # | Step | WORKSHOP.md | Done when |
|---|---|---|---|
| 1 | Fork the repository, clone it, open it in VS Code with the Runme extension, and run the three install cells (uv, Vibe, Mistral CLI). A Codespace is the fallback if you cannot install on your machine | 0.2 | `WORKSHOP.md` opens as a notebook with ▶ buttons; the `install-check` cell prints three versions |
| 2 | Mistral Studio: an API key in the workspace you will use all day | 0.3 | the key is in `.env` as `MISTRAL_API_KEY` |
| 3 | Sentry: a Python project with Error Monitoring, and its DSN | 0.4 | `SENTRY_DSN` is in `.env` |
| 4 | Studio: add Sentry from the connector marketplace and connect it with your Sentry login | 0.5 | the connector lists its tools; its name is in `.env` |
| 5 | Studio: add GitHub from the marketplace and connect it (MistralAI GitHub App on your fork) | 0.6 | its name is in `.env` |
| 6 | `.env` complete, including your own `INVESTIGATION_AGENT_NAME` | 0.7 | no blank values |
| 7 | Install and prove the toolchain; set Vibe's thinking level to medium; sign the Mistral CLI in | 0.8 | `uv pip list` shows `mistralai-agents 1.1.3`; `uv run pytest tests/test_sample_app.py` → `8 passed`; the `setup-vibe` cell → `ready`; Vibe's footer says `[medium]` |
| 8 | Commit, push, send the six errors | 0.9 | six issues in your Sentry project, each with `scenario`, `repository` and `release` tags |

## Tools (installed by the cells in 0.2)

| Tool | Why | Check |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | installs Python 3.12 and every dependency | `uv --version` (0.8 or later; `uv self update`) |
| git, and a GitHub account | the repository, and what the agent reads code from | `git --version`; `git push` works on your fork |
| [Mistral Vibe CLI](https://docs.mistral.ai/vibe/code/cli/install-setup): `uv tool install mistral-vibe` (or another coding agent that can read a folder and run `make`) | you build by prompting it, not by typing code | `vibe --version` |
| [Mistral CLI](https://docs.mistral.ai/studio/mistral-cli/quickstart): `curl -fsSL https://mistral.ai/cli/install.sh \| MISTRAL_INSTALL_BUN=1 bash` | scaffolds, runs and deploys the workflow in modules 4 and 5 (Bun comes with it) | `mistral --version`; the `setup-cli` cell (0.8) signs it in with your API key |
| VS Code with the [Runme](https://marketplace.visualstudio.com/items?itemName=stateful.runme) extension (optional) | `WORKSHOP.md` as ▶ cells | the file opens as a notebook |

Working on your own machine is the preferred setup; a Codespace is the fallback and has all of this preinstalled. Vibe
needs no separate sign-in: it reads `MISTRAL_API_KEY` from the environment, and every Vibe cell runs through
`uv run --env-file .env`, which puts it there. The prompts are plain files in
`workshop/prompts/`, so another coding agent works too.

## Reply to the facilitator with

The output of `uv run pytest tests/test_sample_app.py` and a screenshot of your Sentry project's issue list. That is
how we know the room is ready.

## What you will build, in one picture

```
question ──> investigate workflow ──> agent session ──> Sentry connector (read-only)
                 (module 4)           (modules 1-2)   └─> GitHub connector (read-only)
                                            │
                                            └──> InvestigationReport ──> evals: score + judge + gate (module 3)
```
