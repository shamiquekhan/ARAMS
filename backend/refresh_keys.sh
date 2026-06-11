#!/usr/bin/env bash
# Fetches fresh API keys from https://github.com/alistaitacle/free-llm-api-keys
# and writes them into .env
#
# Usage:  ./refresh_keys.sh          # dry-run (display keys)
#         ./refresh_keys.sh --apply  # update .env in-place

set -euo pipefail

cd "$(dirname "$0)"

URL="https://raw.githubusercontent.com/alistaitacle/free-llm-api-keys/refs/heads/main/README.md"

echo "[*] Fetching latest key list from free-llm-api-keys..."
RAW=$(curl -sSL "$URL" 2>/dev/null) || { echo "ERROR: could not fetch README"; exit 1; }

# --- Extract Gemini keys under the main "API key" section ---
# We look for lines that start with "sk-" inside code blocks after "### Gemini" or "gemini-2.5-flash"
GEMINI_KEYS=$(echo "$RAW" | sed -n '/gemini-2\.5-flash/,/^| /p' | grep -oP 'sk-[A-Za-z0-9]{40,}' | sort -u || true)

# Fallback: grab any sk- key that appears near "gemini"
if [ -z "$GEMINI_KEYS" ]; then
  GEMINI_KEYS=$(echo "$RAW" | grep -oP 'sk-[A-Za-z0-9]{40,}' | sort -u || true)
fi

COUNT=$(echo "$GEMINI_KEYS" | wc -l)

if [ "$COUNT" -eq 0 ]; then
  echo "ERROR: could not find any valid keys in README"
  exit 1
fi

echo "[*] Found $COUNT key(s):"
echo "$GEMINI_KEYS" | sed 's/^/    /'

if [ "${1:-}" = "--apply" ]; then
  CSV=$(echo "$GEMINI_KEYS" | paste -sd ',')
  PRIMARY=$(echo "$GEMINI_KEYS" | head -1)

  if grep -q '^OPENAI_API_KEY=' .env; then
    sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$PRIMARY|" .env
  else
    echo "OPENAI_API_KEY=$PRIMARY" >> .env
  fi

  if grep -q '^OPENAI_API_KEYS=' .env; then
    sed -i "s|^OPENAI_API_KEYS=.*|OPENAI_API_KEYS=$CSV|" .env
  else
    echo "OPENAI_API_KEYS=$CSV" >> .env
  fi

  echo "[✓] .env updated with $COUNT keys (primary: ${PRIMARY:0:20}...)"
  echo "[*] Restart the server for changes to take effect."
else
  echo
  echo "Dry-run mode. Pass --apply to write into .env:"
  echo "  $0 --apply"
fi
