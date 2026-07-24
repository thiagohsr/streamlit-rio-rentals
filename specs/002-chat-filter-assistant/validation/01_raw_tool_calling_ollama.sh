#!/usr/bin/env bash
# Validation step 1 — the very first feasibility check for this feature.
#
# Purpose: confirm the user's self-hosted Ollama endpoint is reachable and
# that its qwen3:8b model actually supports OpenAI-compatible tool/function
# calling at all, before designing anything around it.
#
# Used for: informing the initial "yes, this is technically viable" answer
# in the chat conversation, and research.md #1 (LLM client library).
#
# Run: LLM_BASE_URL=<your ollama endpoint>/v1 ./01_raw_tool_calling_ollama.sh
set -euo pipefail

LLM_BASE_URL="${LLM_BASE_URL:?Set LLM_BASE_URL, e.g. https://your-ollama-host/v1}"
LLM_MODEL="${LLM_MODEL:-qwen3:8b}"

curl -s -X POST "${LLM_BASE_URL%/}/chat/completions" \
  -H "Content-Type: application/json" \
  -d @- <<EOF | python3 -m json.tool
{
  "model": "${LLM_MODEL}",
  "messages": [
    {"role": "user", "content": "I want a 2 bedroom apartment in Copacabana, rent between 500 and 950 reais a month."}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "set_neighborhoods",
        "description": "Set the neighborhood (Bairro) filter to one or more neighborhood names.",
        "parameters": {
          "type": "object",
          "properties": {
            "names": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["names"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "set_numeric_range",
        "description": "Set a min/max range filter for one numeric listing field.",
        "parameters": {
          "type": "object",
          "properties": {
            "field": {"type": "string", "enum": ["rooms", "parking_spots", "suites", "area", "monthly_rent", "condo_fee", "iptu"]},
            "min": {"type": "number"},
            "max": {"type": "number"}
          },
          "required": ["field", "min", "max"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
EOF

# Observed result (first run, before any prompt tuning): 2 of the 3 expected
# tool calls came back (set_neighborhoods + set_numeric_range for
# monthly_rent) — the model did NOT translate "2 bedroom" into a rooms
# range filter on this pass. That gap is what led to FR-005 and the
# exact-count instruction baked into set_numeric_range's description in
# contracts/tools.md.
