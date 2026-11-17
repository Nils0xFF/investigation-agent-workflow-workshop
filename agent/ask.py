"""Ask the investigation agent one question from the terminal and print the report."""

import argparse
import asyncio
import json

from investigate import Investigation, investigate, served_agent
from main import build_agent


def render(outcome: Investigation) -> str:
    """The outcome as readable text: conclusion, root cause, evidence, next check, and the tool calls made."""
    lines: list[str] = []
    if outcome.error is not None:
        lines.append(f"Error: {outcome.error}")
    report = outcome.report
    if report is None:
        lines.append(outcome.text or "(no answer)")
    else:
        lines.append(f"Summary: {report.summary}")
        if report.exception is not None:
            lines.append(f"Exception: {report.exception}")
        if report.file is not None:
            lines.append(f"File: {report.file}")
        if report.symbol is not None:
            lines.append(f"Symbol: {report.symbol}")
        lines.append(f"Confidence: {report.confidence}")
        lines.append(f"Root cause: {report.root_cause}")
        for item in report.evidence:
            lines.append(f"- [{item.source}] {item.reference}: {item.proves}")
        if report.next_check is not None:
            lines.append(f"Next check: {report.next_check}")
    if outcome.tool_calls:
        lines.append("Tool calls:")
        lines.extend(f"- {call.name}({json.dumps(call.arguments)})" for call in outcome.tool_calls)
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="the investigation question")
    parser.add_argument("--served", action="store_true", help="ask the served agent instead of an in-process one")
    parser.add_argument("--json", action="store_true", help="print the raw report JSON instead of the readable report")
    args = parser.parse_args()

    agent = served_agent() if args.served else build_agent()
    outcome = await investigate(args.question, agent=agent)
    if args.json:
        print(json.dumps(outcome.report.model_dump(mode="json") if outcome.report is not None else None, indent=2))
    else:
        print(render(outcome))


if __name__ == "__main__":
    asyncio.run(main())
