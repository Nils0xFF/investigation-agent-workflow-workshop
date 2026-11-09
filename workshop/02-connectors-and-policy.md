# Module 2 — Eyes, with guardrails (35 min)

**Goal.** The agent reads Sentry and GitHub through Studio connectors, can call only reviewed read-only tools, loads
two skills on demand, and leaves an audit trail of every tool call.

**Studio concepts.** Connectors (and how their tools are named), the permission policy (deny by default), hooks,
skills (`SKILL.md` bundles), the sandbox that holds skill files, `agents info`.

**You start from** module 1. **You end with** `agent/config.py`, `agent/hooks.py`, `agent/skills/*/SKILL.md`, an
updated `main.py` and `instructions.md`, and `make check-2` passing.

## Why guardrails before capability

A connector exposes every tool its MCP server has, writes included. An investigation agent that can `update_issue` or
`create_pull_request` is a liability, however good its instructions. So the policy comes with the connectors, not
after them, and the tests prove the policy before any model runs.

## Requirements

- **R2.1 Connector names from the environment.** `agent/config.py` reads `SENTRY_CONNECTOR_NAME` and
  `GITHUB_CONNECTOR_NAME` with `connector_name(env_var)`, which raises a clear `RuntimeError` when one is unset. Studio
  names connectors uniquely per workspace, so names never live in code.
- **R2.2 Read-only allowlists.** `SENTRY_READ_TOOLS` and `GITHUB_READ_TOOLS` are frozensets of literal tool names (no
  globs). Sentry: `find_organizations`, `find_projects`, `get_sentry_resource`, `search_events`, `search_issues`.
  GitHub: `get_commit`, `get_file_contents`, `get_latest_release`, `get_release_by_tag`, `get_tag`, `issue_read`,
  `list_branches`, `list_commits`, `list_issues`, `list_pull_requests`, `list_releases`, `list_tags`,
  `pull_request_read`, `search_code`, `search_commits`, `search_pull_requests`, `search_repositories`. No write,
  identity, user-search or secret-scanning tool, and not Sentry's generic `execute_sentry_tool`/`search_sentry_tools`.
- **R2.3 Tool IDs.** `connector_namespace(name)` returns `connector_<name>` with every non-alphanumeric character
  replaced by `_` and leading/trailing `_` stripped (exactly what the SDK does). `tool_ids(name, tools)` and
  `read_only_tool_ids(sentry, github)` return the sorted `<namespace>.<tool>` IDs.
- **R2.4 Policy.** `permission_policy(sentry, github)` returns `agents.PermissionPolicy(default="deny", ...)` with one
  rule allowing the read-only tool IDs and one allowing `skill.*`. Nothing else, so a reviewed tool name on the *other*
  connector, a `client.` tool, and every sandbox built-in stay denied.
- **R2.5 Audit hook.** `agent/hooks.py` defines `AuditTrail(agents.Hook)` whose `pre_tool_call` logs
  `tool call <tool_id>(<sorted argument names>) in session <id>` on the `investigation.audit` logger at INFO and
  returns `None`. It never logs argument values.
- **R2.6 Skills.** `agent/skills/query-sentry/SKILL.md` and `agent/skills/query-github/SKILL.md`, each with YAML
  frontmatter (`name` = folder name, a one-line `description` saying what it is for and when to use it) and a numbered
  procedure. They name only tools from the allowlists, in backticks, and end with the read-only rule. `instructions.md`
  tells the model to load `query-sentry` and `query-github` (names in backticks) before using a connector.
- **R2.7 Wiring.** `build_agent()` adds: `environment=agents.BashkitSandbox(access="none")` (holds the skill files, gives the
  model no shell or file tools), `skills=` every folder under `agent/skills/`, `connectors=` the two connectors with
  `run_as="auto", auto_auth=False` when `connectors=True` and `[]` otherwise, `permission_policy=`, `hooks=[AuditTrail()]`,
  `builtins=agents.Builtins(subagents=False)`.

## Definition of done

The coding agent's job ends at the first line; the rest you run yourself, from the cells after the prompt.

- `make check-2` passes.
- `make info` lists both connectors, both skills, `AuditTrail`, and a policy that ends with `anything else: deny`.
- Live: `make ask Q="What's causing the latest ValueError in Sentry, and which code is responsible?"` names
  `sample-app/shop/pricing.py :: parse_amount` and quotes `int(value) * 100`. The tool calls line shows
  `skill.read`, `connector_<sentry>.search_issues`, `connector_<github>.get_file_contents`, ...

## Studio clicks

None new: the connectors were connected in the pre-work. If a session fails with *connector ... is not connected*,
open **Studio → Connectors**, reconnect, and check the names in `.env` match exactly.

## The prompt

The same text lives in `workshop/prompts/02-connectors-and-policy.md`: `make vibe-2` opens Vibe with it already submitted, and `make fix-2` continues that session with the failing `make check-2` output appended. With another coding agent, paste it from the file:

```text
Build module 2 of this workshop: connectors, a deny-by-default permission policy, an audit hook and two skills.

Read AGENTS.md, docs/sdk-cheatsheet.md, workshop/02-connectors-and-policy.md and every test in tests/m2/ first.
Then create agent/config.py, agent/hooks.py, agent/skills/query-sentry/SKILL.md, agent/skills/query-github/SKILL.md,
and update agent/main.py and agent/instructions.md so that R2.1 to R2.7 hold and `make check-2` passes (module 1's
tests must keep passing).

Write each SKILL.md as a procedure an on-call engineer would follow: which tool to call first, what to capture from an
event (exception, responsible frames, release), how to open the file on GitHub at the release's commit, and how to cite
evidence. Name only allowlisted tools. Do not edit tests/.
```

## The loop

1. Prompt, build, `make check-2`, paste failures back until it passes.
2. `make info`: read the policy the CLI prints. Is anything allowed that you did not review?
3. Live `make ask`. Watch the tool calls line. Did the model load a skill first? Did it open the file at the release
   commit? If not, that is an instructions or skill problem, and the eval loop in module 3 will measure it.
4. Commit.

## Checkpoint

`git diff module-2 -- agent`; catch up with `git checkout module-2 -- agent`.

## Watch out for

- Skills need a sandbox that can hold files; the default `NoSandbox` refuses them. `BashkitSandbox(access="none")` is the
  smallest one that works, and `access="none"` is what keeps `bash` and `read_file` away from the model.
- The policy also gates the built-in `skill` tool. Forget the `skill.*` rule and the model silently cannot load skills.
- Connectors run under the identity of whoever starts the session. In-process that is your `MISTRAL_API_KEY`; the
  connectors must be connected by that same Studio user.
- A denied call shows up in `tool_calls` (the model asked), it just never ran. That is how you catch an agent that keeps
  trying to write.
