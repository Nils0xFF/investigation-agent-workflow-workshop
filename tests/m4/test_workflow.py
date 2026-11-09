"""Module 4: the workflow runs one agent turn in an activity, keyed by the execution ID, and returns the report.

The module under test lives where the Mistral CLI scaffold puts workflows: workflow/apps/worker/src/worker/workflows/.
"""

import json
from types import SimpleNamespace

import mistralai.agents as agents
import mistralai.workflows as workflows
import pytest

from worker.workflows import investigate as activities
from worker.workflows.investigate import Investigate, InvestigateInput, InvestigateResult, render_report


def completed(text: str | None, *, stop_reason: str | None = None) -> agents.Completed:
    return agents.Completed(
        session_id="s1", turn_id="t1", cursor="c", text=text, output=None, stop_reason=stop_reason, tool_calls=(agents.ToolCall(name="skill.read", arguments={"name": "query-sentry"}),)
    )


def test_read_report_parses_a_completed_turn(valid_report_json: str) -> None:
    assert activities.read_report(completed(valid_report_json))["symbol"] == "rate_for"


@pytest.mark.parametrize(
    ("state", "message"),
    [
        (completed("not json"), "not JSON"),
        (completed(None, stop_reason="iteration_limit"), "without a final answer"),
        (agents.Blocked(session_id="s1", turn_id="t1", cursor="c", text=None, callbacks=()), "approval"),
        (SimpleNamespace(), "did not complete"),
    ],
)
def test_read_report_explains_every_other_outcome(state: object, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        activities.read_report(state)


class FakeSession:
    def __init__(self, state: object) -> None:
        self.state, self.id, self.runs, self.cancelled = state, "s1", [], False

    async def run(self, question: str, **kwargs: object) -> object:
        self.runs.append((question, kwargs))
        return self.state

    async def cancel(self) -> None:
        self.cancelled = True


async def test_the_activity_opens_a_session_on_the_named_agent_and_keys_the_turn(monkeypatch: pytest.MonkeyPatch, valid_report_json: str) -> None:
    session = FakeSession(completed(valid_report_json))
    loaded: list[str] = []

    def load_from(*, agent_name: str) -> object:
        loaded.append(agent_name)

        async def start_session() -> FakeSession:
            return session

        return SimpleNamespace(start_session=start_session)

    monkeypatch.setenv("INVESTIGATION_AGENT_NAME", "investigation-agent-ada")
    monkeypatch.setattr(agents.Agent, "load_from", staticmethod(load_from))

    outcome = await activities.run_investigation("Why is checkout failing?", "exec-1")

    assert loaded == ["investigation-agent-ada"]
    assert session.runs == [("Why is checkout failing?", {"idempotency_key": "exec-1", "timeout": activities.TURN_TIMEOUT_SECONDS})]
    assert session.cancelled
    assert outcome == {"report": json.loads(valid_report_json), "session_id": "s1", "tool_calls": ["skill.read"]}


def test_the_activity_is_not_retried_and_outlives_the_turn() -> None:
    # A retry would start a second investigation on a new session; the workflow's execution ID keys the first one instead.
    params = activities.run_investigation.__wf_activity_params__

    assert params["retry_policy_max_attempts"] == 1
    assert params["start_to_close_timeout_seconds"] > activities.TURN_TIMEOUT_SECONDS


def test_the_worker_discovers_the_workflow_by_convention() -> None:
    # The scaffold's worker serves every workflow class it finds in the `worker.workflows` package: no registration list.
    classes = workflows.discover_all_workflows_in_package("worker.workflows")

    assert Investigate in classes


def test_the_workflow_is_named_investigate() -> None:
    spec = workflows.get_workflow_definition(Investigate)

    assert spec.name == "investigate"
    assert spec.display_name and spec.description
    assert set(spec.input_schema["properties"]) == {"question"}


def test_render_report_reads_well_without_markdown_tables(valid_report_json: str) -> None:
    text = render_report(json.loads(valid_report_json))

    assert text.startswith("Checkout fails for United Kingdom orders")
    assert "Where: sample-app/shop/shipping.py :: rate_for" in text
    assert "- [sentry]" in text and "|" not in text


def test_the_models_round_trip(valid_report_json: str) -> None:
    assert InvestigateInput(question="q").question == "q"
    result = InvestigateResult(report=json.loads(valid_report_json), text="t", session_id="s1", tool_calls=["skill.read"])
    assert InvestigateResult.model_validate_json(result.model_dump_json()) == result
