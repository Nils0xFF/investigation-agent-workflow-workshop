# Module 5 — Stretch: deploy it, trigger it, schedule it (25 min, demo + optional)

**Goal.** See the same code run on Mistral's infrastructure, and connect it to the world: a Slack mention or a schedule
starts the workflow. The facilitator demos this end to end; participants with the right flags follow along, the rest
take the steps home.

**Studio concepts.** `agents deploy` (managed agent worker built from your GitHub commit), workflow deployments,
workspace secrets and secret bindings, webhooks and triggers (with filter expressions), schedules, hardened deployments.

## A. Deploy the agent

Managed deployments build from the commit you pushed, not from your disk, so commit and push first. The Mistral GitHub
app must be installed on the repository (**Studio → Connectors → GitHub**).

```sh
git push
cd agent && uv run --env-file ../.env agents deploy . --name investigation-agent-<you> \
  --secret-binding SENTRY_CONNECTOR_NAME=secret:workspace:sentry_connector_name \
  --secret-binding GITHUB_CONNECTOR_NAME=secret:workspace:github_connector_name
```

Before that, create the two workspace secrets in **Studio → Secrets** with the same values as `.env`. A deployed worker
has no `.env`; the bindings are how it learns the connector names. Pass both bindings on every deploy: a deploy without
them unbinds the secrets.

Then `uv run agents chat investigation-agent-<you>` talks to the deployed agent, and `make ask SERVED=1 Q="..."` and
`make eval ARGS="--served"` run against it. `uv run agents logs investigation-agent-<you> --follow` tails it.

The agent uses connectors, so the deployment is **hardened** by default: sessions run on behalf of the user who starts
them, so each user needs the connectors connected in Studio.

## B. Deploy the workflow

The scaffold deploys itself: from `workflow/`, `mistral deploy --name investigate-<you> --yes` commits `mistral.json`,
pushes, builds `deploy/docker/Dockerfile.worker` from the pushed commit and runs the worker on Mistral. The worker's
`env` package reads `MISTRAL_API_KEY` from the workspace secret of that name when it is not in the environment, so
create it in **Studio → Secrets** (a key of this workspace), and add `INVESTIGATION_AGENT_NAME` (the deployed agent's
name) the same way. Stop your local `make worker` once the deployment is active: two workers on one deployment both
take executions. `mistral apps logs` tails it; `mistral observability traces search` finds its executions.

## C. Trigger it from Slack

The full Slack integration (a router workflow per mention, a long-lived workflow per thread that keeps one agent
session, reply formatting) is the `investigation_agent` cookbook this workshop was cut from; it is the natural next
read. The minimal version, in three Studio objects and one Slack app:

1. **Slack app** at api.slack.com/apps, bot scopes `app_mentions:read`, `channels:history`, `chat:write`. Install it,
   keep the bot token and the signing secret.
2. **Studio → Webhooks → Create**, provider Slack, paste the signing secret, copy the URL (treat it as a credential).
3. **Studio → Triggers → Create**: that webhook, action **Start workflow** `investigate`, filter
   `event.type == 'app_mention' && event.bot_id == null && event.text`. The workflow receives the HTTP request as its
   input, so a Slack-facing variant of `investigate` reads `body.event.text` for the question and posts `text` back with
   `chat.postMessage` in a second activity (bot token from a workspace secret).
4. In the Slack app, **Event Subscriptions**: paste the webhook URL, subscribe to `app_mention`, save. Invite the bot to
   a channel and tag it.

## D. Schedule it

A workflow can carry its own schedules. For a daily "what broke overnight" digest:

```python
@workflows.workflow.define(
    name="investigate",
    ...,
    schedules=[workflows.Schedule(
        schedule_id="nightly-digest",
        cron_expressions=["0 7 * * 1-5"],
        time_zone_name="Europe/Paris",
        input={"question": "What errors are new or regressed in Sentry since yesterday, and which code is responsible for each?"},
    )],
)
```

Studio shows the schedule on the workflow and lets you pause or run it now. A scheduled execution runs as the worker's
service identity, not as a person, so the agent's connectors must be usable by that identity (`run_as="deployment"`
connectors with workspace-scoped credentials), which is why the in-room modules used `run_as="auto"`.

## E. Where to go next

- Put a human in the loop: a `decision="ask"` rule for any future write tool, answered from the workflow with a signal.
- Add a third connector (Grafana, PagerDuty, Rootly) and extend the eval dataset first.
- Replace the hand-written runner with the Evaluations SDK and the Workflows evaluation plugin when your workspace has
  them: same dataset → task → evaluators → gate shape, with results in **Studio → Observability → Evaluate**.
