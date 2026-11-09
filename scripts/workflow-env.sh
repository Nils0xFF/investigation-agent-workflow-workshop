#!/usr/bin/env sh
# Copy the values the workflow worker needs from the repository's .env into workflow/.env, the file the Mistral CLI
# scaffold reads (its `env` package loads it with override=False). Replaces an existing line, appends a missing one,
# never touches the scaffold's own settings (DEPLOYMENT_NAME, telemetry, ...).
set -eu
cd "$(dirname "$0")/.."
[ -f .env ] || { echo "No .env at the repository root: run scripts/bootstrap-env.sh first." >&2; exit 1; }
[ -f workflow/.env ] || { echo "No workflow/.env: run \`mistral init workflow --preset workflow --no-git --yes\` first." >&2; exit 1; }
copied=0
for name in MISTRAL_API_KEY INVESTIGATION_AGENT_NAME; do
  value=$(sed -n "s/^$name=//p" .env | head -n 1)
  [ -n "$value" ] || { echo "$name is empty in .env; fill it in first." >&2; continue; }
  if grep -q "^$name=" workflow/.env; then
    awk -v n="$name" -v v="$value" 'BEGIN{FS=OFS="="} $1==n {print n"="v; next} {print}' workflow/.env > workflow/.env.tmp && mv workflow/.env.tmp workflow/.env
  else
    printf '%s=%s\n' "$name" "$value" >> workflow/.env
  fi
  copied=$((copied + 1))
done
echo "workflow/.env: $copied value(s) copied from .env ($(sed -n 's/^DEPLOYMENT_NAME=//p' workflow/.env | head -n 1) is the deployment the worker registers on)."
