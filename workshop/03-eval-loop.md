# Module 3 — The eval loop (45 min)

**Goal.** A repeatable measurement of how well the agent investigates the six planted bugs, a gate that says whether
the instructions are good enough, and two rounds of improving the instructions against that gate.

**Studio concepts.** Datasets, scorers and judges as code; structured output as the thing you score; Studio
**Observability** to read a session's trace when a case fails. (Studio's hosted Evaluations SDK does the same at scale
for Enterprise workspaces; the loop you build here is the same shape: dataset → task → evaluators → gate.)

**You start from** module 2. **You end with** `evals/scoring.py`, `evals/judge.py`, `evals/run_evals.py`, two saved
runs in `evals/results/`, better instructions, and `make check-3` passing.

## Why this is the heart of the workshop

Module 2 ended with you reading one report and judging it by eye. That does not scale, does not compare versions, and
does not survive a model update. A requirements document for a model (the instructions, the skills) is only as good as
the evidence that it works, and the evidence is an eval you can re-run. Same for the prompts you give your coding
agent: `make check-N` is their eval.

## The dataset

`evals/cases.jsonl` is fixed. Each case is a question plus what a correct investigation must find:

| field | meaning |
|---|---|
| `question` | what an engineer would ask |
| `expected_exception` | the exception type Sentry shows |
| `expected_file`, `expected_symbol` | where the defect is |
| `cause_keywords` | words a correct root cause mentions; at least two must appear |
| `reference_cause` | the planted bug, explained by the person who planted it; the judge grades against it |

## Requirements

- **R3.1 Scorers.** `evals/scoring.py`: `load_cases(path=CASES_PATH, ids=None)`; `file_matches(expected, actual)` (same
  trailing path components, at least the file and its folder; accepts `./`, a leading repo prefix and a GitHub `blob` URL;
  a bare file name is not enough); `symbol_matches` (ignores a module prefix and `()`); `exception_matches` (type name,
  case-insensitive); `cause_matches(keywords, text, minimum=2)`; `score(case, report, *, tool_calls=0, error=None,
  session_id=None) -> CaseResult` (a missing report scores zero everywhere); `summarize(results, gate=GATE) -> Summary`
  with one accuracy per scorer, the mean judge score (`None` when nothing was judged), the mean tool calls, and
  `failed_gates` as `"<name> <value> < <threshold>"` strings. `GATE = {"file": 0.8, "symbol": 0.8, "exception": 0.8,
  "cause": 0.8, "judge": 3.5}`.
- **R3.2 Judge.** `evals/judge.py`: a `Verdict(score: 1..5, rationale)` model, a rubric that rewards the right defect,
  the quoted line and cited evidence and penalises claims without evidence, `judge_prompt(case, report)` (system =
  rubric; user = question, reference cause, reference location, the report as JSON) and `async judge(case, report, *,
  client=None)` that calls `client.chat.parse_async(response_format=Verdict, model=JUDGE_MODEL, messages=...,
  temperature=0)` on the `mistralai.client.Mistral` client. The judge never sees Sentry or GitHub data.
- **R3.3 Runner.** `evals/run_evals.py`: `--cases 1,2`, `--served`, `--no-judge`, `--concurrency N` (default 3),
  `--label`. `run_case` never raises: an exception becomes a result with `error`. `run()` gathers cases under a
  semaphore. `render_table()` prints one row per case plus the aggregates and `gate: PASS|FAIL`; `render_delta()`
  compares with the previous saved run; `save_run()` writes `evals/results/<timestamp>.json`. Exit code 0 when the gate
  passes, 1 otherwise. It imports the agent from `agent/` (add that folder to `sys.path`).

## Definition of done

The coding agent's job ends at the first line; the rest you run yourself, from the cells after the prompt.

- `make check-3` passes.
- `make eval ARGS="--no-judge --cases 1,2"` runs two live cases and prints the table.
- `make eval` (all six, with judge) runs twice: once before and once after you improve the instructions, and the second
  run's delta line shows what changed.

## The prompt

The same text lives in `workshop/prompts/03-eval-loop.md`: `make vibe-3` opens Vibe with it already submitted, and `make fix-3` continues that session with the failing `make check-3` output appended. With another coding agent, paste it from the file:

```text
Build module 3 of this workshop: the eval loop.

Read AGENTS.md, docs/sdk-cheatsheet.md, workshop/03-eval-loop.md, evals/cases.jsonl and every test in tests/m3/ first.
Then create evals/scoring.py, evals/judge.py and evals/run_evals.py so that R3.1 to R3.3 hold and `make check-3` passes.

The scorers are pure functions over the InvestigationReport; keep the matching rules exactly as the card and the tests
state them (strict on facts, lenient on formatting). The judge grades against the reference cause only. The runner
must finish and print a table even when a case raises. Do not edit tests/ or evals/cases.jsonl.
```

## The loop (this time, the agent's loop)

1. Prompt, build, `make check-3` until it passes.
2. Baseline: `make eval ARGS="--label baseline"`. Read the table. Which scorer fails most? Open a failing case's session
   in **Studio → Observability** (the session ID is in the results JSON) and read what the model actually did.
3. Form one hypothesis per failure and change *one thing* in `instructions.md` or a `SKILL.md`. Typical findings:
   - it reports the caller's frame, not the defect's → the `[REPORT]` rule about `file`/`symbol` is not explicit enough;
   - it reads the file on `main` instead of the release commit → the skill does not say the release is a commit SHA;
   - it never quotes the line → `root_cause` description needs "quote the offending line";
   - it stops early (`iteration_limit`) → the procedure asks for too much; cut steps, or raise `max_iterations`.
4. `make eval ARGS="--label 'instructions v2'"`. The delta line tells you whether the change helped. Keep it if it did;
   revert it if not. Two rounds fit in the module; the gate is reachable.
5. Commit the instructions with the results JSON of the passing run.

## Checkpoint

`git diff module-3 -- evals agent/instructions.md agent/skills`.

## Watch out for

- Six cases × a few tool calls each is a few minutes per run. Use `--cases` and `--no-judge` while iterating and the
  full run to decide.
- `temperature=0.1` keeps runs comparable but not identical. A change that moves a score by one case is noise; look for
  moves across cases.
- The judge is a model. Read its rationale on a 2 before you trust it; if it is wrong, fix the rubric, not the score.
- Keep the reference causes out of the instructions. Teaching the agent the answers is not improving it.
