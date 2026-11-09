---
title: Building Production-Ready Agentic Workflows
sub_title: An investigation agent on Mistral Studio, built by prompting, proved by evals
author: Mistral · a hands-on workshop
theme:
  name: dark
---

<!-- speaker_note: "Run from the repository root: `make present` (presenterm -x workshop/present/deck.md). Every code block runs with ctrl+e. Blocks marked acquire_terminal hand the screen to Vibe and bring you back here when it exits." -->

Setup check
===

Six planted bugs, in place, and the toolchain works:

```bash +exec
cd "$(git rev-parse --show-toplevel)"
uv run pytest tests/test_sample_app.py -q 2>&1 | tail -n 3
```

<!-- pause -->

Six issues in Sentry (sent in the pre-work; re-send if your project is empty):

```bash +exec
cd "$(git rev-parse --show-toplevel)"
make send-error N=all 2>&1 | tail -n 7
```

<!-- end_slide -->

The problem
===

An error lands in Sentry. Then a person does the legwork.

<!-- column_layout: [1, 1] -->
<!-- column: 0 -->

**The same chain, every alert**

1. Open the issue, read a representative event and its stack trace
2. Find the file on GitHub, at the commit that was actually deployed
3. Work out which assumption in the code the input violated
4. Write it up in the thread, with links

Twenty to forty minutes of on-call attention, repeated. The first ten are pure navigation.

<!-- column: 1 -->

**The obvious fix is an agent. The usual agent dies in production.**

- API tokens pasted into prompts and env files
- Nothing stops it from resolving the issue or commenting on the PR
- A crash five tool calls in loses the whole investigation
- "It worked on the three examples I tried" is the only evidence
- Nobody can see what it did, so nobody trusts the answer

<!-- reset_layout -->
<!-- speaker_note: "Ask who has done the left column this month. Name the five failure modes on the right; the next slide answers each one in order." -->

<!-- end_slide -->

Why Studio
===

One answer per failure, in the same order.

| failure | Studio piece | what it gives you |
|---|---|---|
| credentials | **Connectors** | Sentry and GitHub tokens stay in Studio; the agent calls tools as the session's user |
| blast radius | **Permission policy + hooks** | deny by default, a reviewed read-only list, every call audited |
| durability | **Workflows** | an investigation is an execution: recorded, resumable, triggerable, schedulable |
| evidence | **Structured output + evals** | every answer is typed data, so a dataset can score it and a gate can fail it |
| visibility | **Observability** | every session and tool call traced |
| the demo gap | **One code path** | `agents chat` → `agents serve` → `agents deploy`, same agent, no rewrite |

<!-- pause -->

And you build all of it by writing requirements and reading test results, not by pasting code.

<!-- end_slide -->

What we're building
===

```
question ──> investigate workflow ──> agent session ──> Sentry connector  (read-only)
              (durable, module 4)     (modules 1-2)   └─> GitHub connector  (read-only)
                                            │
                                            └──> InvestigationReport ──> evals: score + judge + gate (module 3)
```

<!-- pause -->

The report every turn must end with:

```json
{"exception": "KeyError: 'UK'",
 "file": "sample-app/shop/shipping.py", "symbol": "rate_for",
 "root_cause": "RATES_CENTS has the ISO code 'GB', not 'UK': `return RATES_CENTS[country]`",
 "confidence": "high", "evidence": [ ...2 items... ], "next_check": null}
```

You can score data. You cannot score prose.

<!-- end_slide -->

The method: the same loop, at two levels
===

<!-- column_layout: [1, 1] -->
<!-- column: 0 -->

**You → your coding agent**

- A requirements card per module: outcome, interfaces, constraints, the test that says done
- The agent generates; you never paste code
- `make check-N` is the eval: fail, fix, pass
- Checkpoint tags catch you up

<!-- column: 1 -->

**You → the model**

- `instructions.md` is a requirements document
- Skills carry the long procedures, loaded on demand
- `make eval` is the eval: six cases, scorers, a judge, a gate
- Change one thing, rerun, read the delta

<!-- reset_layout -->

<!-- pause -->

A requirement is done when a test says so. That sentence is the whole workshop.

<!-- end_slide -->

What a good requirement looks like
===

<!-- column_layout: [2, 3] -->
<!-- column: 0 -->

**Weak**

> Build me an agent that investigates Sentry errors.

Produces something every time. Nothing you can check, compare, or hand to the next person.

<!-- column: 1 -->

**Strong: the module 1 card**

- **Outcome** · one turn ends in a validated `InvestigationReport`, even offline with a scripted model
- **Interfaces** · `build_agent(connectors=False)`, `investigate(question, agent=…) -> Investigation`, the report fields
- **Constraints** · `mistral-large-4`, `max_iterations ≤ 40`, nothing raises: failures become `Investigation.error`
- **Test** · `make check-1` passes, `make ask` prints a report

<!-- reset_layout -->

<!-- end_slide -->

The plan
===

| clock | module | you build | done when |
|---|---|---|---|
| 0:00 | Welcome, setup clinic | six errors in Sentry | `test_sample_app` passes |
| 0:15 | 1 · A testable agent | main, instructions, report, investigate, ask | `make check-1` |
| 0:45 | 2 · Eyes, with guardrails | connectors, policy, hook, two skills | `make check-2` |
| 1:20 | Break | | |
| 1:30 | 3 · The eval loop | scorers, judge, runner, gate; two rounds on the instructions | `make check-3` + the gate |
| 2:15 | 4 · Make it durable | the `investigate` workflow, worker, execution in Studio | `make check-4` |
| 2:50 | 5 · Stretch (demo) | `agents deploy`, Slack trigger, schedule | it answers in Slack |
| 3:15 | Wrap | | |

<!-- end_slide -->

The loop, every module
===

1. **Paste the card's prompt** — it tells the agent to read `AGENTS.md`, the cheat sheet, the card and the tests first
2. **`make check-N`** — the tests are the specification; failing on the first try is normal
3. **Paste the failure back** — "`make check-N` fails with: … Fix the implementation, not the test." Two or three rounds
4. **Passing → live check → commit** — `make info`, `make ask`; read what the model produced

<!-- pause -->

In this deck, each step is a block: `ctrl+e` runs it.

| | |
|---|---|
| `make vibe-N` | opens Vibe with module N's prompt already submitted |
| `make fix-N` | continues the Vibe session with the failing output appended |
| `make check-N` | the acceptance tests of modules 1..N |

Behind? `git checkout module-N -- agent`. Never edit `tests/`, `evals/cases.jsonl`, `sample-app/shop/`.

<!-- end_slide -->

Module 1 · A testable agent · 30 min
===

**Goal** · an agent that answers with a validated `InvestigationReport`, built so a test can drive it with a scripted model and no network.

**Concepts** · `Agent` · `response_format` · sessions and turn records · `agents.testing.ScriptedModel` · `agents info` / `agents chat`

**You build** · `agent/report.py` · `instructions.md` · `main.py` · `investigate.py` · `ask.py`

**Done when** · `make check-1` · `make ask` prints a report

<!-- pause -->

The prompt (`workshop/prompts/01-agent-skeleton.md`):

<!-- include: ../prompts/01-agent-skeleton.md -->

<!-- end_slide -->

Module 1 · build it
===

Hand the card to Vibe (takes over the screen; `/quit` or ctrl+c brings you back here):

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make vibe-1
```

Acceptance tests:

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make check-1 2>&1 | tail -n 25
```

Still failing? Feed the failure back into the same Vibe session:

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make fix-1
```

<!-- end_slide -->

Module 1 · live check
===

What the CLI loaded:

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make info 2>&1 | grep -v catalogue
```

One question, in-process (no connectors yet, so expect low confidence and a `next_check`):

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make ask Q="What's causing the latest ValueError in Sentry, and which code is responsible?" 2>&1 | grep -v catalogue
```

```bash +exec
cd "$(git rev-parse --show-toplevel)" && git add -A && git commit -qm "Module 1: a testable agent" && git log --oneline -1
```

<!-- speaker_note: "The low-confidence answer is the baseline. Module 2 is the before/after." -->

<!-- end_slide -->

Module 2 · Eyes, with guardrails · 35 min
===

**Goal** · reads Sentry and GitHub through Studio connectors, calls only reviewed read-only tools, loads two skills on demand, audits every call.

**Concepts** · connectors and tool naming (`connector_<name>.<tool>`) · `PermissionPolicy(default="deny")` · hooks · `SKILL.md` bundles · the sandbox that holds skill files

**You build** · `agent/config.py` · `hooks.py` · `skills/query-sentry/SKILL.md` · `skills/query-github/SKILL.md` · `main.py` + `instructions.md` updated

**Done when** · `make check-2` · `make info` ends with `anything else: deny` · `make ask` names `pricing.py :: parse_amount`

<!-- pause -->

The prompt (`workshop/prompts/02-connectors-and-policy.md`):

<!-- include: ../prompts/02-connectors-and-policy.md -->

<!-- end_slide -->

Module 2 · build it
===

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make vibe-2
```

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make check-2 2>&1 | tail -n 25
```

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make fix-2
```

<!-- end_slide -->

Module 2 · the policy, printed and proved
===

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make info 2>&1 | grep -v catalogue | sed -n '/connectors:/,$p'
```

Now the agent can look. Same question as before:

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make ask Q="What's causing the latest ValueError in Sentry, and which code is responsible?" 2>&1 | grep -v catalogue
```

```bash +exec
cd "$(git rev-parse --show-toplevel)" && git add -A && git commit -qm "Module 2: connectors behind a deny-by-default policy" && git log --oneline -1
```

<!-- speaker_note: "Point at the tool calls line: skill.read first, then connector_sentry search_issues, then connector_github get_file_contents. A denied call would still be listed there; it just never ran." -->

<!-- end_slide -->

Module 3 · The eval loop · 45 min
===

Module 2 ended with you reading one report by eye. That does not scale, does not compare versions, and does not survive a model update.

**The shape** · dataset → task → evaluators → gate. Six cases (`evals/cases.jsonl`), deterministic scorers for the facts, an LLM judge for the explanation, a threshold that fails the run.

**You build** · `evals/scoring.py` · `judge.py` · `run_evals.py` — then `instructions.md` and the skills, twice.

**Done when** · `make check-3` · `make eval` → `gate: PASS` · a delta line between two runs

<!-- pause -->

The prompt (`workshop/prompts/03-eval-loop.md`):

<!-- include: ../prompts/03-eval-loop.md -->

<!-- end_slide -->

Module 3 · six planted bugs, six cases
===

| # | exception | where | the assumption that breaks |
|---|---|---|---|
| 1 | ValueError | `pricing.py :: parse_amount` | prices are whole dollars; "12.50" reaches `int()` |
| 2 | KeyError | `shipping.py :: rate_for` | country codes are ISO; checkout still sends "UK" |
| 3 | ZeroDivisionError | `discounts.py :: average_item_price` | a cart has items; it was emptied in another tab |
| 4 | TypeError | `inventory.py :: reserve` | stock levels are numbers; the warehouse CSV is text |
| 5 | AttributeError | `notifications.py :: confirmation_recipient` | every order has a customer; guests have none |
| 6 | IndexError | `taxes.py :: rate_for_region` | region codes are "CA-ON"; France is "FR" |

The scorers check the facts. The judge grades the explanation against a reference cause and never sees Sentry or GitHub.

<!-- end_slide -->

Module 3 · build it
===

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make vibe-3
```

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make check-3 2>&1 | tail -n 25
```

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make fix-3
```

<!-- end_slide -->

Module 3 · baseline
===

Two cases, no judge, while the code settles:

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make eval ARGS="--no-judge --cases 1,2" 2>&1 | grep -v catalogue | tail -n 12
```

The full run is the baseline. Read the table: which scorer fails most?

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make eval ARGS="--label baseline" 2>&1 | grep -v catalogue | tail -n 14
```

<!-- speaker_note: "While it runs: open Studio → Observability, find a failing case's session (the ID is in evals/results/*.json) and read what the model actually did." -->

<!-- end_slide -->

Module 3 · one change, rerun, read the delta
===

Typical findings → the one line to change:

- Reports the caller's frame (`checkout.py`) → the `[REPORT]` rule on `file`/`symbol` is not explicit
- Reads the file on `main`, not at the release commit → the skill never says the release is a SHA
- Never quotes the line → `root_cause`'s description needs "quote the offending line"
- `iteration_limit` → the procedure asks for too much; cut steps

Edit `agent/instructions.md` or a `SKILL.md` (one hypothesis, one change), then:

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make eval ARGS="--label 'instructions v2'" 2>&1 | grep -v catalogue | tail -n 14
```

The delta line decides: keep or revert. Gate: file, symbol, exception, cause ≥ 0.80 · judge ≥ 3.5.

```bash +exec
cd "$(git rev-parse --show-toplevel)" && git add -A && git commit -qm "Module 3: the eval loop" && git log --oneline -1
```

<!-- end_slide -->

Module 4 · Make it durable · 35 min
===

**Goal** · one investigation runs as a Workflow execution: started from Studio with a question, recorded step by step, resumable after a crash, returning the report. The agent runs as a durable worker of its own.

**Concepts** · `agents serve` · workflow, activity, worker, deployment · executions in Studio · idempotency keys

**You build** · `workflow/models.py` · `activities.py` · `investigate_workflow.py` · `worker.py`

**Done when** · `make check-4` · an execution completes in Studio · it resumes after you kill the worker

<!-- pause -->

The prompt (`workshop/prompts/04-workflow.md`):

<!-- include: ../prompts/04-workflow.md -->

<!-- end_slide -->

Module 4 · build it
===

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make vibe-4
```

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make check-4 2>&1 | tail -n 25
```

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)" && make fix-4
```

<!-- end_slide -->

Module 4 · run it
===

Both workers in the background (the agent under your `INVESTIGATION_AGENT_NAME`, the workflow on your `DEPLOYMENT_NAME`):

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make bg-start 2>&1 | grep -v catalogue
```

Studio → Workflows → `investigate` → Start Workflow:

```json
{"question": "Checkout is failing with KeyError: 'UK'. What's the root cause?"}
```

Watch the execution, then the workers' logs:

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make bg-logs
```

Break it on purpose: stop the workers mid-execution, start them again, watch the execution resume from the activity.

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make bg-stop; sleep 2; make bg-start 2>&1 | tail -n 4
```

<!-- end_slide -->

Module 5 · Deploy it, trigger it, schedule it · demo
===

| | |
|---|---|
| **agents deploy** | a managed worker built from your pushed commit; connector names arrive as `--secret-binding`; hardened by default |
| **workflow deployment** | Studio → Workflows → Deployments → Create: your repo, `workflow/Dockerfile`, secrets bound |
| **Slack webhook + trigger** | a Slack app, a Studio webhook with its signing secret, a trigger on `app_mention` with a filter |
| **schedule** | `schedules=[workflows.Schedule(cron_expressions=["0 7 * * 1-5"], input={...})]` on the workflow |

```bash +exec +acquire_terminal
cd "$(git rev-parse --show-toplevel)/agent" && uv run --env-file ../.env agents deploy . --name "investigation-agent-$USER" \
  --secret-binding SENTRY_CONNECTOR_NAME=secret:workspace:sentry_connector_name \
  --secret-binding GITHUB_CONNECTOR_NAME=secret:workspace:github_connector_name
```

```bash +exec
cd "$(git rev-parse --show-toplevel)" && make eval ARGS="--served --cases 2 --no-judge" 2>&1 | grep -v catalogue | tail -n 8
```

<!-- speaker_note: "Needs the Mistral GitHub app on the repo and org flags; have the recording ready." -->

<!-- end_slide -->

<!-- jump_to_middle -->

Requirements in, evidence out.
===

<!-- alignment: center -->

A requirement has four parts: outcome, interfaces, constraints, and the test that says it is done.

Guardrails are requirements too: deny by default, written as data, proved before any model runs.

An eval you can re-run is the evidence: dataset, scorers, a judge, a gate, a delta line.

<!-- end_slide -->

Where to go next
===

- A human in the loop: a `decision="ask"` rule for any future write tool, answered from the workflow with a signal
- A third connector (Grafana, PagerDuty); extend the eval dataset first
- The full Slack version, thread-aware, one session per thread: the investigation-agent cookbook
- Enterprise workspaces: the Evaluations SDK and the Workflows evaluation plugin, same dataset → task → evaluators → gate shape

In the repository: `workshop/00-prework.md … 05-stretch.md` · `workshop/facilitator-notes.md` · `docs/sdk-cheatsheet.md` · `AGENTS.md` · tags `module-1 … module-4`

Which module changed how you will write your next prompt?
