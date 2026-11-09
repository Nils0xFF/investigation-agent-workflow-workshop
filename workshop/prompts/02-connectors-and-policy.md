Build module 2 of this workshop: connectors, a deny-by-default permission policy, an audit hook and two skills.

Read AGENTS.md, docs/sdk-cheatsheet.md, workshop/02-connectors-and-policy.md and every test in tests/m2/ first.
Then create agent/config.py, agent/hooks.py, agent/skills/query-sentry/SKILL.md, agent/skills/query-github/SKILL.md,
and update agent/main.py and agent/instructions.md so that R2.1 to R2.7 hold and `make check-2` passes (module 1's
tests must keep passing).

Write each SKILL.md as a procedure an on-call engineer would follow: which tool to call first, what to capture from an
event (exception, responsible frames, release), how to open the file on GitHub at the release's commit, and how to cite
evidence. Name only allowlisted tools. Do not edit tests/.

Done when `make check-2` and `make lint` pass: then stop and tell me in three lines what you built. Do not run
`make ask`, `make info`, `make eval`, `make serve` or anything else that calls the model; do not look at git tags,
branches or history; do not re-verify the SDK by introspection, the cheat sheet is checked against the pinned version.
