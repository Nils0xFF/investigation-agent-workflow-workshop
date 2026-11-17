"""Run one investigation turn and read the turn record into plain data."""

from dataclasses import dataclass

import mistralai.agents as agents

from main import DEFAULT_AGENT_NAME
from report import InvestigationReport


@dataclass
class Investigation:
    """One turn of the agent as data: what was asked, what came back, and whether it is a valid report."""

    question: str
    session_id: str
    report: InvestigationReport | None
    text: str
    tool_calls: tuple[agents.ToolCall, ...]
    error: str | None

    @property
    def ok(self) -> bool:
        """True when the turn ended with a valid InvestigationReport."""
        return self.report is not None and self.error is None


async def investigate(question: str, *, agent: agents.Agent, timeout: int = 600) -> Investigation:
    """Ask `question` in a fresh session. Every turn outcome becomes an Investigation; nothing raises."""
    session = await agent.start_session()
    try:
        state = await session.run(question, output_type=InvestigationReport, timeout=timeout)
        report: InvestigationReport | None = None
        error: str | None = None
        match state:
            case agents.Completed(output=InvestigationReport() as parsed):
                report = parsed
            case agents.Completed(output=agents.InvalidOutput(error=parse_error)):
                error = f"the answer is not a valid InvestigationReport: {parse_error}"
            case agents.Completed(stop_reason=reason):
                error = f"the turn ended without a final answer (stop_reason={reason!r})"
            case agents.Failed(error=turn_error):
                error = f"the turn failed: {turn_error.message}"
            case agents.Blocked():
                error = "the turn is blocked, waiting on an approval or a client tool"
            case agents.Running():
                error = f"the turn was still running after {timeout}s"
            case agents.Busy():
                error = "another turn is already running on this session"
        return Investigation(
            question=question,
            session_id=getattr(state, "session_id", None) or session.id,
            report=report,
            text=getattr(state, "text", ""),
            tool_calls=getattr(state, "tool_calls", ()),
            error=error,
        )
    finally:
        await session.cancel()


def served_agent(name: str | None = None) -> agents.Agent:
    """The agent that `agents serve` runs, loaded by its served name."""
    return agents.Agent.load_from(agent_name=name or DEFAULT_AGENT_NAME)
