"""The investigation agent: one model, one instructions file, one structured report per turn."""

import os
from pathlib import Path

import mistralai.agents as agents

from report import InvestigationReport

ROOT = Path(__file__).resolve().parent
MODEL = "mistral-large-4"
DEFAULT_AGENT_NAME = os.environ.get("INVESTIGATION_AGENT_NAME", "investigation-agent")


def build_agent(*, connectors: bool = True, name: str | None = None) -> agents.Agent:
    """Build the agent. Building touches no network; connectors resolve when a session starts.

    `connectors` has no effect yet: module 2 wires the Sentry and GitHub connectors in.
    """
    return agents.Agent(
        name=name or DEFAULT_AGENT_NAME,
        model=MODEL,
        description="Answers one investigation question about a production error with a validated report.",
        instructions=(ROOT / "instructions.md").read_text(encoding="utf-8"),
        output_type=InvestigationReport,
        max_iterations=32,
        temperature=0.1,
    )


# The CLI (`agents info`, `agents chat`, `agents serve`) imports this object at module scope.
agent = build_agent()
