# Facilitator notes

## The pitch, in one breath

Everyone has built a demo agent by pasting code. Nobody trusts one in production. The difference is requirements you
can test and an eval you can re-run. This workshop builds a real investigation agent on Mistral Studio that way, twice
over: you hand your coding agent requirements cards with acceptance tests, and the agent you build gets instructions
with an eval gate. By the end, participants have a durable, read-only Sentry+GitHub investigator running under a
workflow, and a method they can take to any agent.

## Timeline (210 min)

| Clock | Block | Minutes | What happens |
|---|---|---|---|
| 0:00 | Welcome, setup clinic | 15 | Everyone runs `uv run pytest tests/test_sample_app.py` and sees six issues in Sentry. Fix stragglers while you present the map. |
| 0:15 | Module 1: a testable agent | 30 | Intro slide → the loop slide (footers say `[medium]`) → everyone presses `vibe-1` → present *good requirement* while it builds → `check-1` → live `ask-1`. |
| 0:45 | Module 2: eyes, with guardrails | 35 | Intro slide → `vibe-2` → present *who holds the credential*, *deny by default* and *skills* while it builds → `check-2` → `info-2` → live `ask-2` finds `pricing.py`. |
| 1:20 | Break | 10 | |
| 1:30 | Module 3: the eval loop | 45 | Intro slide → `vibe-3` → present the six cases and the loop while it builds → `check-3` → baseline eval → one change → second run → delta. |
| 2:15 | Module 4: make it durable | 35 | `init-workflow` + `workflow-env` → intro slide → `vibe-4` → present the two workers and Studio while it builds → `check-4` → `serve` + `worker` → execution in Studio → kill the worker. |
| 2:50 | Module 5: stretch (demo) | 25 | You deploy, trigger from Slack, show the schedule. Flagged participants follow. |
| 3:15 | Wrap | 15 | The method, next steps, feedback. |

If module 3 runs long (it will want to), take the time from module 5: the demo compresses to 10 minutes.

Prompt first, talk second: every module's intro slide ends with a cue to press `vibe-N`, and the slides after it are
the ones you present while the coding agent builds (5-10 minutes at medium thinking). The deck order already follows
this: `good-requirement` sits after the loop slide for module 1; `m2-connectors`, `m2-guardrails` and `m2-skills` after
module 2's intro; `m3-dataset` + `m3-loop` and `m4-run` after theirs. Nobody watches a progress bar.

## Running the room from one window

Present from `WORKSHOP.md` open as a Runme notebook in VS Code (or a Codespace) on the projector: the slides deck
carries the framing, `WORKSHOP.md` carries the doing. Each step is a cell with a ▶ button; Vibe cells open in the VS
Code terminal panel at full size (`.vscode/settings.json` turns off Runme's small notebook terminal for interactive
cells, which Vibe's UI does not fit) and give control back when you quit Vibe, check cells print inline, the module 4
workers are `background` cells that keep running while you move on. Vibe needs no `--setup`: every Vibe cell runs through
`uv run --env-file .env`, and Vibe reads `MISTRAL_API_KEY` from the environment; the `setup-vibe` cell is the proof.
The cells are the literal commands, not `make` wrappers, so people see what runs; the Makefile keeps the same commands
as targets for terminal users. Participants have the identical file, so "press ▶ on
`check-2`" means the same thing on every screen, and anyone without VS Code runs the same cell names as `make`
targets. Rehearse once in a fresh Codespace: it is also the fastest way to find a missing dependency.

Local setup is the recommended path (WORKSHOP.md 0.2 A installs uv, Vibe and the Mistral CLI as three cells);
Codespaces is the fallback for locked-down laptops. Codespaces notes: the devcontainer runs the same three installs, so
`mistral` is on the PATH there, but it is the less-rehearsed path, so try it once yourself before the day. A GitHub
Free personal account includes 120 core-hours a month (60 hours on the 2-core machine), ample for the day; the fork
must be on the participant's own account for the quota to be theirs. Ask participants to add the four secrets before
they create the codespace, or `.env` is written with blanks to fill in. Secrets named in
`.devcontainer/devcontainer.json` are prompted for when the codespace is created.

`workshop/present/deck.md` is an optional presenterm version of the same flow for a facilitator who prefers a
terminal-only setup (`make present`, needs presenterm); it is not needed by participants.

## Keeping the coding-agent prompts short

A rehearsal of `vibe-1` on Mistral Large 4 at the default *high* thinking level took 30 minutes. Three things made it
long, and the repository now guards against all three: the agent re-verified the SDK by introspection because the cheat
sheet listed one stale attribute name (fixed), it went on to the card's live "definition of done" after the tests were
passing and hit a `.env` path bug in the Makefile (fixed: every target now loads the root `.env` by absolute path), and
it found the `module-1` tag and compared itself to the reference solution. The prompts, `AGENTS.md` and the cards now
say: stop when `make check-N` and `make lint` pass, never call the model, never read tags or branches, never create a
second `.env`. Keep those lines when you edit a prompt.

Thinking level: tell the room to run `/thinking` → *medium* before the first prompt (WORKSHOP.md says so above the
`vibe-1` cell); Vibe's footer shows the level next to the model name. To make it the default on your own machine, give
the model an entry in `~/.vibe/config.toml` with `thinking = "medium"` (see the Vibe configuration reference for the
`[[models]]` shape, which also needs `name`, `provider` and `alias`). If a prompt still runs long, the `fix-N` cell is
cheaper than a restart: it continues the same session with only the failing output.

## What to demo live, and what to show as a recording

- **Live:** the end state at the start of the day (`make ask` on a deployed agent, 60 seconds), each module's
  `make check-N` reaching `N passed` on your own machine, the module 3 delta line, the module 4 execution timeline.
- **Recorded (fallback):** the Slack trigger end to end, `agents deploy`. Both depend on org flags and network; have
  a 2-minute recording of each.

## The method, on one slide

A good requirement for a model (or a coding agent) has four parts: the outcome, the interfaces it must respect, the
constraints it must not break, and the test that says it is done. Every card follows that shape; so do the agent's
instructions (role, read-only, procedure, report) with the evals as the test. Weak prompt for contrast:
*"Build me an agent that investigates Sentry errors."* It produces something every time, and nothing you can check.

## Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `connector ... is not connected` at session start | the connector was connected by another Studio user, or the API key is from another workspace | reconnect in Studio as the key's owner; `.env` names must match exactly |
| The private Sentry connector is invisible to the SDK | the API key was created with the default *shared connectors only* scope | create a key with the *private and shared connectors* scope, or make the connector shared in the workspace |
| A connector is missing from the marketplace, or Connect fails | the organization restricts connectors, or the Sentry/GitHub login used is not the one that owns the project or fork | an org admin enables it (Admin → Connectors); connect Sentry with the account that owns the `workshop-shop` project and GitHub with the account that owns the fork |
| The agent reads another participant's fork | the Sentry events carry no `repository` tag (no GitHub `origin` remote when `send-error` ran) | re-send the errors from a clone whose `origin` is the fork; the tag is `owner/repo` and the skills tell the model to use it |
| `make check-N` fails on the first prompt | normal; the loop is the point | paste the failure back, 2-3 rounds |
| `agents init` refuses: folder exists, or no network | a half-done earlier run, or the lock step cannot reach PyPI | `rm -rf agent` and run the cell again once online; the scaffold is only files |
| `mistral init` fails or `mistral` is not found | not signed in, Bun missing, or `~/.mistral/bin` not on PATH | re-run the `setup-cli` cell (`mistral login --api-key -` fed from `.env`; `mistral login --device` answers *not available yet*); re-run the installer with `MISTRAL_INSTALL_BUN=1`; open a new terminal |
| `mistral dev` cannot start the worker | `workflow/.env` has no `MISTRAL_API_KEY`, or the first run is still downloading Python 3.14 | `sh scripts/workflow-env.sh`; wait for the download once |
| The activity fails with `RestrictedWorkflowAccessError` at startup | `mistralai.agents` imported at module level in the workflow module | move the import inside the activity and `read_report`; the card says so |
| The coding agent rewrote `agent/pyproject.toml` or the Dockerfile | the prompt's constraint was lost in a long session | `git checkout -- agent/pyproject.toml agent/Dockerfile agent/uv.lock`; a dependency goes in with `cd agent && uv add` |
| `agents serve` refuses to start | workflows not enabled on the key's workspace | use a key from a Workflows-enabled workspace; otherwise stay in-process (modules 1-3 do not need it) |
| `agents deploy` says not enabled / asks for the GitHub app | org feature flags or app not installed | demo only; participants take it home |
| Eval run very slow | 30 people × 6 cases × 3 concurrent sessions = rate limits | `--cases 1,2 --no-judge` while iterating; full run once; `--concurrency 2` |
| The agent reports the calling frame (`checkout.py`) instead of the defect | instructions not explicit about "the frame the code you read, not the caller" | this is the module 3 exercise; let them find it |
| `UnsupportedAgentFeatureError ... skills` | `NoSandbox` with skills | `environment=agents.BashkitSandbox(access="none")` |
| Everything JSON in `agents chat` | `output_type` on the agent | expected; `make ask` renders it |
| Sentry event quota or delays | free tier; events take ~1 min to be searchable | send errors in the pre-work, not in the room |
| A test on `tests/m4` imports `activities` from `workflow/` and gets the wrong module | a stray `activities.py` elsewhere on the path | the pythonpath order in `pyproject.toml` is agent, workflow, evals, sample-app; keep module names unique |

## SDK version skew

The reference code pins the public release `mistralai-agents==1.1.3` and is verified against it (75 tests, `agents
info`). The 1.1 release renamed two keywords from the release candidates, `response_format=` → `output_type=` and
`sandbox=` → `environment=`; coding agents trained on the candidates, or on the older Agents API, will reach for the old
names, which is why the cheat sheet and `AGENTS.md` spell out the current ones. Bump the pin deliberately: re-run
`make test` and `agents info` after any bump, and update the cheat sheet if a signature moved.

Two tests in `tests/m2/test_policy.py` import private SDK helpers to pin the agent's policy to the runtime's own
rules: `_safe_namespace` (how connector tool namespaces are built) and `always_denies` (the policy matcher). If a bump
moves them, those two tests are the ones to update; the behaviour test (`test_an_unreviewed_tool_never_runs`) uses only
public API and stays.

## Checkpoints

Participants fork the repository and work on `main` of their fork; `main` has no agent code (no `agent/` folder at
all until `agents init` in module 1), only the specification (cards, prompts, tests) and the sample app, and the GitHub connector reads the sample app from their fork at the commit
that sent the errors, which is why the setup cell pushes before `make send-error`. Open your own checkout on `main`
when you project it, so what you show is what they have; switch to `solution` only to show the reference.

`main` is the starter (tag `start`). The `solution` branch holds one commit per module, tagged `module-1` …
`module-4`; each tag passes `make check-N`. A participant who is behind runs `git checkout module-N -- agent` (or
`evals`, `workflow`) and continues. Before the workshop, push `main`, `solution` and the tags to the repository they
fork (`git push origin main solution --tags`).

## Before the workshop

- [ ] Run the full day yourself from a fresh fork with a fresh Sentry project; keep the results JSON of your passing
      eval run to show as the target.
- [ ] Record the two fallback videos.
- [ ] Confirm the model name `mistral-large-4` and the judge `mistral-medium-latest` are available to participant
      workspaces; change `MODEL` in `agent/main.py` and `JUDGE_MODEL` in `evals/judge.py` if not.
- [ ] Check Sentry's connector tool names in a participant-like workspace (`agents info` prints the policy; a live
      `make ask` prints the tool IDs the model called). Update `config.py` if the catalog changed. Both connectors come
      from Studio's marketplace (Connectors → New connector → Browse marketplace). Walk through WORKSHOP.md 0.3-0.6
      yourself in a fresh workspace and fix any label Studio has renamed since.
- [ ] Send the pre-work a week ahead, with a "reply with the output of `uv run pytest tests/test_sample_app.py`" ask.
