"""Module 1: the agent exists, its instructions are its requirements, and every turn ends in an InvestigationReport."""

import re

import mistralai.agents as agents
import pytest
from pydantic import ValidationError

from ask import render
from investigate import investigate
from main import DEFAULT_AGENT_NAME, MODEL, ROOT, build_agent
from report import InvestigationReport

REPORT_FIELDS = set(InvestigationReport.model_fields)


def test_the_agent_is_named_and_typed() -> None:
    agent = build_agent(connectors=False)

    assert agent.name == DEFAULT_AGENT_NAME
    assert agent.model == MODEL
    assert agent.output_type is InvestigationReport
    assert agent.max_iterations and agent.max_iterations <= 40


def test_the_instructions_are_the_requirements_file() -> None:
    agent = build_agent(connectors=False)
    text = (ROOT / "instructions.md").read_text(encoding="utf-8")

    assert agent.instructions == text
    for section in ("[ROLE]", "[READ-ONLY]", "[INVESTIGATION]", "[REPORT]"):
        assert section in text, f"instructions.md lacks a {section} section"
    # The model fills the report, so the instructions must explain every field by name.
    missing = REPORT_FIELDS - set(re.findall(r"`([a-z_]+)`", text))
    assert not missing, f"instructions.md does not explain report fields: {sorted(missing)}"


async def test_a_scripted_answer_becomes_a_parsed_report(valid_report_json: str) -> None:
    model = agents.testing.ScriptedModel([agents.testing.reply(valid_report_json)])

    outcome = await investigate("Why is checkout failing?", agent=build_agent(connectors=False).override(model=model))

    assert outcome.ok and outcome.error is None
    assert outcome.report is not None and outcome.report.symbol == "rate_for" and outcome.report.confidence == "high"
    assert outcome.tool_calls == ()
    assert outcome.session_id
    model.assert_consumed()


async def test_an_answer_that_is_not_a_report_is_an_error_not_an_exception() -> None:
    model = agents.testing.ScriptedModel([agents.testing.reply("I could not find the error.")])

    outcome = await investigate("Why is checkout failing?", agent=build_agent(connectors=False).override(model=model))

    assert not outcome.ok and outcome.report is None
    assert outcome.error and "not a valid InvestigationReport" in outcome.error
    assert outcome.text == "I could not find the error."


def test_the_report_validates_its_fields() -> None:
    with pytest.raises(ValidationError):
        InvestigationReport(summary="x", root_cause="y", confidence="certain")  # type: ignore[arg-type]


async def test_render_shows_the_conclusion_and_the_evidence(valid_report_json: str) -> None:
    model = agents.testing.ScriptedModel([agents.testing.reply(valid_report_json)])
    outcome = await investigate("Why?", agent=build_agent(connectors=False).override(model=model))

    text = render(outcome)

    assert "Checkout fails for United Kingdom orders" in text
    assert "Root cause" in text and "RATES_CENTS" in text
    assert "[sentry]" in text and "[github]" in text
