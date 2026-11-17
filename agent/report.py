"""The output contract of the investigation agent: every turn ends with an InvestigationReport."""

from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """One piece of proof a conclusion in the report rests on."""

    source: Literal["sentry", "github", "other"] = Field(description="Where this evidence comes from: a Sentry issue, the GitHub repository, or somewhere else.")
    reference: str = Field(description="A stable pointer to the evidence: the Sentry issue URL, the GitHub file URL at a commit, or another locator.")
    proves: str = Field(description="What exactly this evidence proves about the defect.")


class InvestigationReport(BaseModel):
    """The answer to one investigation question, as validated data."""

    summary: str = Field(description="What fails, for which input, and why, in one or two sentences.")
    exception: str | None = Field(default=None, description="The exception the error report shows, e.g. \"KeyError: 'UK'\", or null if none was found.")
    file: str | None = Field(default=None, description="Repo-relative path of the file that contains the defect, or null if unknown.")
    symbol: str | None = Field(default=None, description="The function or method the stack trace points at, or null if unknown.")
    root_cause: str = Field(description="The defect as a fact about the code: quote the line that is wrong and say why it is wrong for this input.")
    confidence: Literal["low", "medium", "high"] = Field(description="How well the evidence supports the report: high only when code evidence proves the cause, low when little could be checked.")
    evidence: list[Evidence] = Field(description="One entry per piece of proof the conclusions rest on.")
    next_check: str | None = Field(default=None, description="The single most useful next thing to check when the report is incomplete, or null when the investigation is complete.")
