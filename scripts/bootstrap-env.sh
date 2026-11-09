#!/usr/bin/env sh
# Create .env from .env.example when it is missing, filling each variable from the environment when it is set there
# (Codespaces secrets arrive as environment variables). Never overwrites an existing .env.
set -eu
cd "$(dirname "$0")/.."
if [ -f .env ]; then
  echo ".env already exists; leaving it alone."
  exit 0
fi
: > .env
filled=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ''|'#'*) printf '%s\n' "$line" >> .env ;;
    *=*)
      name=${line%%=*}
      value=$(eval "printf '%s' \"\${$name:-}\"")
      if [ -n "$value" ]; then
        printf '%s=%s\n' "$name" "$value" >> .env
        filled=$((filled + 1))
      else
        printf '%s\n' "$line" >> .env
      fi
      ;;
    *) printf '%s\n' "$line" >> .env ;;
  esac
done < .env.example
echo "Wrote .env ($filled values filled from the environment). Open it and complete the rest."
