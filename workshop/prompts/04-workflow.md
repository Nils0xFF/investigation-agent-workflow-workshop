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

Done when `make check-4` and `make lint` pass: then stop and tell me in three lines what you built. Do not run
`make ask`, `make info`, `make eval`, `make serve` or anything else that calls the model; do not look at git tags,
branches or history; do not re-verify the SDK by introspection, the cheat sheet is checked against the pinned version.
