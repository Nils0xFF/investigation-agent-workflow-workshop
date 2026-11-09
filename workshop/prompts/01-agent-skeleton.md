Build module 1 of this workshop: a testable investigation agent.

Read AGENTS.md, docs/sdk-cheatsheet.md, workshop/01-agent-skeleton.md and every test in tests/m1/ before writing code.
agent/ was scaffolded with `agents init`: keep its pyproject.toml, Dockerfile, uv.lock, .gitignore and .python-version
as they are, replace the hello-world main.py, and create agent/report.py, agent/instructions.md, agent/investigate.py
and agent/ask.py so that the requirements R1.0 to R1.5 in the card hold and `make check-1` passes.

Constraints: use the API exactly as the cheat sheet shows it (mistralai-agents 1.1: `output_type=`, start_session() +
session.run(), match on agents.Completed / Failed / Blocked). Do not edit tests/. When a test fails, read the test and
fix the implementation. Write the instructions as a requirements document for the model: short sections, one rule per
line, every report field explained.

Done when `make check-1` and `make lint` pass: then stop and tell me in three lines what you built. Do not run
`make ask`, `make info`, `make eval`, `make serve` or anything else that calls the model; do not look at git tags,
branches or history; do not re-verify the SDK by introspection, the cheat sheet is checked against the pinned version.
