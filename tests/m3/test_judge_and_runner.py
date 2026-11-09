"""Module 3: the judge grades against the reference, and the runner survives a broken case and reports the gate."""

import json
from types import SimpleNamespace

import pytest

import run_evals
from investigate import Investigation
from judge import Verdict, judge, judge_prompt
from report import InvestigationReport
from scoring import load_cases


def test_the_judge_sees_the_reference_and_the_report_but_no_raw_data(valid_report_json: str) -> None:
    case = load_cases(ids={2})[0]
    report = InvestigationReport.model_validate_json(valid_report_json)

    messages = judge_prompt(case, report)

    assert messages[0]["role"] == "system" and "Score 1 to 5" in messages[0]["content"]
    assert case.reference_cause in messages[1]["content"]
    assert "rate_for" in messages[1]["content"] and json.loads(valid_report_json)["summary"] in messages[1]["content"]


class FakeChat:
    def __init__(self, verdict: Verdict) -> None:
        self.verdict, self.calls = verdict, []

    async def parse_async(self, *, response_format, **kwargs):
        self.calls.append(kwargs)
        assert response_format is Verdict
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=self.verdict))])


async def test_the_judge_returns_the_models_verdict(valid_report_json: str) -> None:
    case = load_cases(ids={2})[0]
    chat = FakeChat(Verdict(score=4, rationale="Right defect, no quoted line."))

    verdict = await judge(case, InvestigationReport.model_validate_json(valid_report_json), client=SimpleNamespace(chat=chat))

    assert verdict.score == 4
    assert chat.calls[0]["temperature"] == 0 and chat.calls[0]["messages"][1]["role"] == "user"


async def test_the_runner_scores_every_case_even_when_one_breaks(monkeypatch: pytest.MonkeyPatch, valid_report_json: str) -> None:
    cases = load_cases(ids={1, 2})

    async def fake_investigate(question: str, *, agent: object) -> Investigation:
        if "ValueError" in question:
            raise RuntimeError("connector sentry_a1b2 is not connected")
        return Investigation(question=question, session_id="s2", report=InvestigationReport.model_validate_json(valid_report_json), tool_calls=())

    monkeypatch.setattr(run_evals, "investigate", fake_investigate)

    results = await run_evals.run(cases, agent=object(), use_judge=False, concurrency=2)
    summary = run_evals.summarize(results)
    table = run_evals.render_table(results, summary)

    assert [r.case_id for r in results] == [1, 2]
    assert not results[0].ok and "RuntimeError: connector" in (results[0].error or "")
    assert results[1].ok and results[1].file and results[1].symbol
    assert summary.completed == 1 and not summary.passed
    assert "gate: FAIL" in table and "case" in table.splitlines()[0]


def test_the_delta_compares_with_the_previous_run() -> None:
    previous = {"run_at": "2026-01-01T00-00-00Z", "summary": {"file": 0.5, "symbol": 0.5, "exception": 0.5, "cause": 0.5, "judge": 3.0}}
    summary = run_evals.summarize([run_evals.CaseResult(case_id=1, question="q", ok=True, file=True, symbol=True, exception=True, cause=True, judge=4)])

    assert run_evals.render_delta(summary, None) == "no previous run to compare with"
    assert "file 0.50 -> 1.00 (+0.50)" in run_evals.render_delta(summary, previous)
    assert "judge 3.00 -> 4.00 (+1.00)" in run_evals.render_delta(summary, previous)
