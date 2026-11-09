"""Module 2: the skills are valid bundles, name only tools the policy allows, and the agent can load them."""

import logging
import re

import mistralai.agents as agents

from config import GITHUB_READ_TOOLS, SENTRY_READ_TOOLS
from investigate import investigate
from main import ROOT, build_agent

SKILLS_DIR = ROOT / "skills"
SKILLS = sorted(path.name for path in SKILLS_DIR.iterdir() if path.is_dir())
ALLOWED = SENTRY_READ_TOOLS | GITHUB_READ_TOOLS


def test_the_two_skills_are_bundled() -> None:
    assert SKILLS == ["query-github", "query-sentry"]


def test_each_skill_has_frontmatter_and_a_body() -> None:
    for skill in SKILLS:
        text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        head, _, body = text.removeprefix("---\n").partition("\n---\n")
        assert f"name: {skill}" in head, skill
        assert re.search(r"^description: \S", head, re.MULTILINE), f"{skill} needs a description: the model picks skills by it"
        assert body.strip(), f"{skill} has an empty body"


def test_skills_only_name_allowed_tools() -> None:
    for skill in SKILLS:
        text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        named = set(re.findall(r"`([a-z]+(?:_[a-z]+)+)`", text))
        assert named <= ALLOWED, f"{skill} names tools the policy denies: {sorted(named - ALLOWED)}"


def test_the_instructions_tell_the_model_when_to_load_each_skill() -> None:
    instructions = (ROOT / "instructions.md").read_text(encoding="utf-8")
    for skill in SKILLS:
        assert f"`{skill}`" in instructions, f"instructions.md never tells the model to load {skill}"


async def test_the_model_can_load_a_skill_and_the_hook_logs_it(valid_report_json: str, caplog) -> None:
    model = agents.testing.ScriptedModel([agents.testing.call("skill", name="query-sentry"), agents.testing.reply(valid_report_json)])

    with caplog.at_level(logging.INFO, logger="investigation.audit"):
        outcome = await investigate("Why?", agent=build_agent(connectors=False).override(model=model))

    assert outcome.ok
    assert [call.name for call in outcome.tool_calls] == ["skill.read"]
    assert any("tool call skill.read(name)" in record.message for record in caplog.records), "AuditTrail did not log the call"
    model.assert_consumed()
