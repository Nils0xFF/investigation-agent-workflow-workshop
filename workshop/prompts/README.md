# The prompts

One file per module, verbatim from the cards in `workshop/`, so the deck, the Makefile and a participant pasting by hand
all feed the coding agent the same text.

| File | Module | Hand it to Vibe with |
|---|---|---|
| `01-agent-skeleton.md` | 1 · A testable agent | `make vibe-1` |
| `02-connectors-and-policy.md` | 2 · Eyes, with guardrails | `make vibe-2` |
| `03-eval-loop.md` | 3 · The eval loop | `make vibe-3` |
| `04-workflow.md` | 4 · Make it durable | `make vibe-4` |
| `fix.md` | the loop, any module | `make fix-N` (appends the failing `make check-N` output and continues the last Vibe session) |

`make vibe-N` runs `vibe "<prompt>"`: the interactive TUI opens with the prompt already submitted, so you watch it
read the card, the cheat sheet and the tests, then build. Using another coding agent? Paste the file's contents; they
are plain text.
