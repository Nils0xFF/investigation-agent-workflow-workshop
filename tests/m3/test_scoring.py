"""Module 3: the scorers are strict about facts and lenient about formatting, and the gate is applied as written."""

import pytest

from report import InvestigationReport
from scoring import CASES_PATH, GATE, CaseResult, cause_matches, exception_matches, file_matches, load_cases, score, summarize, symbol_matches


def test_the_six_cases_load_and_point_at_the_sample_app() -> None:
    cases = load_cases(CASES_PATH)

    assert [case.id for case in cases] == [1, 2, 3, 4, 5, 6]
    assert all(case.expected_file.startswith("sample-app/shop/") for case in cases)
    assert all(len(case.cause_keywords) >= 3 for case in cases)
    assert load_cases(CASES_PATH, ids={2, 5}) == [cases[1], cases[4]]


@pytest.mark.parametrize(
    ("actual", "matches"),
    [
        ("sample-app/shop/shipping.py", True),
        ("shop/shipping.py", True),
        ("./sample-app/shop/shipping.py", True),
        ("https://github.com/acme/shop/blob/abc123/sample-app/shop/shipping.py", True),
        ("shipping.py", False),  # a bare file name is too weak a claim
        ("sample-app/shop/pricing.py", False),
        ("tests/shipping.py", False),
        (None, False),
    ],
)
def test_file_matching_needs_the_folder_and_the_file(actual: str | None, matches: bool) -> None:
    assert file_matches("sample-app/shop/shipping.py", actual) is matches


@pytest.mark.parametrize(("actual", "matches"), [("rate_for", True), ("shipping.rate_for", True), ("rate_for()", True), ("rate", False), (None, False)])
def test_symbol_matching_ignores_module_prefix_and_parentheses(actual: str | None, matches: bool) -> None:
    assert symbol_matches("rate_for", actual) is matches


def test_exception_and_cause_matching() -> None:
    assert exception_matches("KeyError", "KeyError: 'UK'")
    assert not exception_matches("KeyError", "ValueError: bad")
    assert cause_matches(("UK", "GB", "legacy"), "The legacy code 'UK' is not the ISO code 'GB'.")
    assert not cause_matches(("UK", "GB", "legacy"), "A lookup failed.")


def test_scoring_a_full_report(valid_report_json: str) -> None:
    case = load_cases(CASES_PATH, ids={2})[0]
    report = InvestigationReport.model_validate_json(valid_report_json)

    result = score(case, report, tool_calls=7, session_id="s1")

    assert (result.ok, result.file, result.symbol, result.exception, result.cause) == (True, True, True, True, True)
    assert result.tool_calls == 7 and result.report and result.report["symbol"] == "rate_for"


def test_scoring_a_missing_report_is_all_zero() -> None:
    case = load_cases(CASES_PATH, ids={1})[0]

    result = score(case, None, error="The turn failed")

    assert not result.ok and not any((result.file, result.symbol, result.exception, result.cause))
    assert result.error == "The turn failed"


def result(case_id: int, *, hits: bool, judge: int | None) -> CaseResult:
    return CaseResult(case_id=case_id, question="q", ok=True, file=hits, symbol=hits, exception=hits, cause=hits, judge=judge, tool_calls=4)


def test_the_gate_passes_at_the_thresholds() -> None:
    results = [result(i, hits=i != 6, judge=4) for i in range(1, 7)]  # 5/6 = 0.83 on every scorer

    summary = summarize(results)

    assert summary.passed and summary.failed_gates == []
    assert summary.file == pytest.approx(5 / 6) and summary.judge == 4 and summary.completed == 6


def test_the_gate_fails_and_names_what_failed() -> None:
    results = [result(i, hits=i < 4, judge=3) for i in range(1, 7)]  # 3/6 on every scorer, judge 3.0

    summary = summarize(results)

    assert not summary.passed
    assert summary.failed_gates == [
        f"file 0.50 < {GATE['file']:.2f}",
        f"symbol 0.50 < {GATE['symbol']:.2f}",
        f"exception 0.50 < {GATE['exception']:.2f}",
        f"cause 0.50 < {GATE['cause']:.2f}",
        f"judge 3.00 < {GATE['judge']:.2f}",
    ]


def test_the_judge_gate_is_skipped_without_a_judge() -> None:
    summary = summarize([result(1, hits=True, judge=None)])

    assert summary.judge is None and summary.passed
