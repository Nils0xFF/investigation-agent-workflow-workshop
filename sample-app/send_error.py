"""Send one or all sample-shop errors to Sentry so the investigation agent has something to investigate.

    uv run --env-file ../.env python send_error.py 1      # one scenario
    uv run --env-file ../.env python send_error.py all    # all six

Each event is tagged with the scenario number, the GitHub repository (owner/repo of the `origin` remote) and the current
git commit as the release, so the agent can open the exact code on GitHub.
"""

import logging
import os
import subprocess
import sys

import sentry_sdk

from shop.checkout import SCENARIOS


def git_sha() -> str | None:
    """The current commit, so Sentry's release matches the code on GitHub."""
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or None


def git_repository() -> str | None:
    """The GitHub repository of the `origin` remote as owner/repo, so the agent knows which fork holds the code."""
    result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=False)
    url = result.stdout.strip()
    if "github.com" not in url:
        return None
    path = url.split("github.com", 1)[1].lstrip(":/").removesuffix(".git").strip("/")
    return path if path.count("/") == 1 else None


def send(number: int, repository: str | None) -> str | None:
    """Run one scenario and send its exception to Sentry. Returns the event ID."""
    scenario = SCENARIOS[number]
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("scenario", str(number))
        scope.set_tag("scenario_name", scenario.__name__)
        if repository:
            scope.set_tag("repository", repository)
        try:
            scenario()
        except Exception:
            return sentry_sdk.capture_exception()
    raise RuntimeError(f"Scenario {number} did not raise: has the bug been fixed?")


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        raise SystemExit("SENTRY_DSN is not set. Add your Sentry project's DSN to ../.env.")
    if len(argv) != 2 or (argv[1] != "all" and argv[1] not in {str(n) for n in SCENARIOS}):
        raise SystemExit(f"Usage: send_error.py <1..{len(SCENARIOS)}|all>")

    sentry_sdk.init(dsn=dsn, release=git_sha(), environment="demo")
    repository = git_repository()
    if not repository:
        logging.warning("No GitHub `origin` remote found: events will carry no `repository` tag, so the agent must search for the fork.")
    numbers = list(SCENARIOS) if argv[1] == "all" else [int(argv[1])]
    for number in numbers:
        event_id = send(number, repository)
        logging.info("Scenario %d (%s) sent to Sentry as event %s.", number, SCENARIOS[number].__name__, event_id)
    sentry_sdk.flush()


if __name__ == "__main__":
    main(sys.argv)
