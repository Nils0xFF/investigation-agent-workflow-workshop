"""Module 2: the agent can read Sentry and GitHub, and nothing else. The permission policy is deny-by-default."""

import mistralai.agents as agents
import pytest
from mistralai.vibe_agents.sdk.assembly.connectors import _safe_namespace
from mistralai.vibe_agents.sdk.authoring.permissions import always_denies

from config import GITHUB_READ_TOOLS, SENTRY_READ_TOOLS, connector_namespace, permission_policy, read_only_tool_ids
from main import build_agent

SENTRY, GITHUB = "sentry_a1b2", "github_app"

WRITE_TOOLS = {
    # GitHub writes.
    "create_issue",
    "update_issue",
    "add_issue_comment",
    "create_pull_request",
    "merge_pull_request",
    "create_or_update_file",
    "push_files",
    "create_branch",
    # Sentry's generic dispatchers can reach any Sentry tool, including writes.
    "execute_sentry_tool",
    "search_sentry_tools",
    # Identity, people data and secret scanning are not investigation evidence.
    "get_me",
    "search_users",
    "list_repository_collaborators",
    "run_secret_scanning",
}


def test_the_allowlists_are_read_only_and_literal() -> None:
    assert WRITE_TOOLS.isdisjoint(SENTRY_READ_TOOLS | GITHUB_READ_TOOLS)
    assert all("*" not in tool and "?" not in tool for tool in SENTRY_READ_TOOLS | GITHUB_READ_TOOLS)


@pytest.mark.parametrize("name", [SENTRY, GITHUB, "My Sentry (prod)", "github-app-2"])
def test_the_namespace_matches_the_sdk(name: str) -> None:
    # The SDK puts a connector's tools under `connector_<name>`; the policy must match that exactly or it denies everything.
    assert connector_namespace(name) == f"connector_{_safe_namespace(name)}"


def test_tool_ids_cover_both_connectors() -> None:
    ids = read_only_tool_ids(SENTRY, GITHUB)

    assert f"connector_{SENTRY}.search_issues" in ids
    assert f"connector_{GITHUB}.get_file_contents" in ids
    assert len(ids) == len(SENTRY_READ_TOOLS) + len(GITHUB_READ_TOOLS)


@pytest.mark.parametrize(
    ("tool_id", "denied"),
    [
        (f"connector_{SENTRY}.search_issues", False),
        (f"connector_{SENTRY}.get_sentry_resource", False),
        (f"connector_{GITHUB}.get_file_contents", False),
        (f"connector_{GITHUB}.pull_request_read", False),
        ("skill.read", False),
        (f"connector_{SENTRY}.update_issue", True),
        (f"connector_{SENTRY}.execute_sentry_tool", True),
        (f"connector_{GITHUB}.create_pull_request", True),
        (f"connector_{GITHUB}.get_me", True),
        # A reviewed tool name is still refused when it comes from the other connector.
        (f"connector_{GITHUB}.search_issues", True),
        ("connector_grafana.query_prometheus", True),
        ("client.search_issues", True),
        ("file_system.bash", True),
        ("file_system.read_file", True),
    ],
)
def test_the_policy_denies_everything_but_reviewed_read_tools(tool_id: str, denied: bool) -> None:
    policy = permission_policy(SENTRY, GITHUB)

    assert policy.default == "deny"
    assert always_denies(policy, tool_id) is denied


RAN: list[str] = []


# Decorated tools must live at module scope: the SDK reads their source to describe them.
@agents.tool(model_access="direct")
async def delete_issue(issue_id: str) -> str:
    """Delete a Sentry issue."""
    RAN.append(issue_id)
    return "deleted"


async def test_an_unreviewed_tool_never_runs() -> None:
    # A tool the policy does not list, wired straight into an agent with our policy: the model calls it, the SDK refuses it.
    agent = agents.Agent(model="mistral-large-4", instructions="x", tools=[delete_issue], permission_policy=permission_policy(SENTRY, GITHUB))
    model = agents.testing.ScriptedModel([agents.testing.call("delete_issue", issue_id="1"), agents.testing.reply("ok")])

    session = await agent.override(model=model).start_session()
    try:
        state = await session.run("Delete issue 1")
    finally:
        await session.cancel()

    assert isinstance(state, agents.Completed)
    assert RAN == [], "the policy let a write tool run"
    assert [call.name for call in state.tool_calls] == ["client.delete_issue"]
    model.assert_consumed()


def test_the_agent_builds_with_and_without_connectors() -> None:
    assert build_agent(connectors=True).permission_policy == permission_policy(SENTRY, GITHUB)
    assert build_agent(connectors=False).permission_policy == permission_policy(SENTRY, GITHUB)
