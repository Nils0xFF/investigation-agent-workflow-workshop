Build module 3 of this workshop: the eval loop.

Read AGENTS.md, docs/sdk-cheatsheet.md, workshop/03-eval-loop.md, evals/cases.jsonl and every test in tests/m3/ first.
Then create evals/scoring.py, evals/judge.py and evals/run_evals.py so that R3.1 to R3.3 hold and `make check-3` passes.

The scorers are pure functions over the InvestigationReport; keep the matching rules exactly as the card and the tests
state them (strict on facts, lenient on formatting). The judge grades against the reference cause only. The runner
must finish and print a table even when a case raises. Do not edit tests/ or evals/cases.jsonl.

Done when `make check-3` and `make lint` pass: then stop and tell me in three lines what you built. Do not run
`make ask`, `make info`, `make eval`, `make serve` or anything else that calls the model; do not look at git tags,
branches or history; do not re-verify the SDK by introspection, the cheat sheet is checked against the pinned version.
