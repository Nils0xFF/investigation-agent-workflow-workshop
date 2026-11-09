.PHONY: setup check check-1 check-2 check-3 check-4 test lint format info chat ask serve eval send-error worker \
        vibe-check vibe-1 vibe-2 vibe-3 vibe-4 fix-1 fix-2 fix-3 fix-4 present bg-start bg-stop bg-logs

# The agent's connector names and keys come from .env (scripts/bootstrap-env.sh). Every target loads it; the workflow
# worker reads workflow/.env instead (scripts/workflow-env.sh copies the shared values across).
ENV := --env-file $(CURDIR)/.env
PROMPTS := workshop/prompts

setup:            ## Install every dependency (one shared venv for tests, evals, the agent and the workflow)
	uv sync --all-groups

# One `check-N` per workshop module: the tests of modules 1..N plus the sample-app guard.
check-1:
	uv run pytest tests/test_sample_app.py tests/m1
check-2:
	uv run pytest tests/test_sample_app.py tests/m1 tests/m2
check-3:
	uv run pytest tests/test_sample_app.py tests/m1 tests/m2 tests/m3
check-4:
	uv run pytest tests/test_sample_app.py tests/m1 tests/m2 tests/m3 tests/m4

test:             ## Every test, then load the agent the way `agents deploy` does (needs the connector names in .env)
	uv run pytest
	cd agent && uv run $(ENV) agents info .

check: lint test

lint:
	uv run ruff format --check .
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

info:             ## What the CLI loaded: model, connectors, skills, hooks, policy
	cd agent && uv run $(ENV) agents info .

chat:             ## Talk to the agent in-process (Ctrl+D to quit)
	cd agent && uv run $(ENV) agents chat

ask:              ## One question, in-process: make ask Q="..."   (add SERVED=1 to ask the served agent)
	cd agent && uv run $(ENV) python ask.py $(if $(SERVED),--served,) "$(Q)"

serve:            ## Run the agent as a durable local worker under INVESTIGATION_AGENT_NAME (leave it running)
	cd agent && uv run $(ENV) sh -c 'exec agents serve . --name "$${INVESTIGATION_AGENT_NAME:?Set INVESTIGATION_AGENT_NAME in .env}"'

eval:             ## The loop: run every case, score, judge, gate. make eval ARGS="--cases 1,2 --no-judge"
	uv run $(ENV) python evals/run_evals.py $(ARGS)

send-error:       ## Send sample-shop errors to Sentry: make send-error N=3   (N=all for all six)
	cd sample-app && uv run $(ENV) python send_error.py $(or $(N),all)

worker:           ## Run the workflow worker from the Mistral CLI scaffold (reads workflow/.env; hot reload)
	cd workflow && mistral dev

# --- Building by prompting: the same commands as the cells in WORKSHOP.md. `uv run --env-file .env` puts MISTRAL_API_KEY
# --- in the environment, which is where Vibe reads it, so no `vibe --setup` is needed. `vibe-N` opens Vibe with module
# --- N's card prompt as its first message; `fix-N` continues the last Vibe session with the failing `make check-N`
# --- output appended to the fix prompt. HEADLESS=1 runs the same prompt without Vibe's UI, tool calls auto-approved.
VIBE_MODE := $(if $(HEADLESS),--trust --auto-approve --output streaming -p,)

vibe-check:       ## Prove Vibe reaches Mistral with the key in .env (one tiny headless turn)
	@uv run $(ENV) vibe --trust --max-turns 1 --output text -p "Reply with exactly one word: ready"

vibe-1 vibe-2 vibe-3 vibe-4:
	@uv run $(ENV) vibe $(VIBE_MODE) "$$(cat $(PROMPTS)/0$(subst vibe-,,$@)-*.md)"
fix-1 fix-2 fix-3 fix-4:
	@uv run $(ENV) vibe -c $(VIBE_MODE) "$$(cat $(PROMPTS)/fix.md; $(MAKE) check-$(subst fix-,,$@) 2>&1 | tail -n 80)"

# --- Optional: the same flow as WORKSHOP.md as terminal slides, for a facilitator without VS Code (needs presenterm).
present:          ## Open the terminal deck; ctrl+e runs the block under the cursor
	presenterm -x workshop/present/deck.md

bg-start:         ## Module 4 in one pane: start the agent worker and the workflow worker in the background
	mkdir -p .present
	nohup $(MAKE) serve > .present/serve.log 2>&1 &
	nohup $(MAKE) worker > .present/worker.log 2>&1 &
	sleep 10; tail -n 6 .present/serve.log .present/worker.log

bg-logs:          ## The last lines of both background workers
	tail -n 12 .present/serve.log .present/worker.log

bg-stop:          ## Stop both background workers
	-pkill -f "agents serve"
	-pkill -f "workflow/worker.py|python worker.py"
