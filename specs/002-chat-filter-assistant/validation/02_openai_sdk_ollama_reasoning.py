"""Validation step 2 — confirm the `openai` SDK (not just raw curl) surfaces
Qwen3's non-standard `reasoning` field, since that's what FR-010's debug
view depends on.

Used for: research.md #1 (LLM client library choice) and #2 (surfacing the
reasoning trace). This is also where the model was observed correctly
translating "2 bedroom" into a rooms range filter on its own, without any
prompt changes yet (informing the FR-005 exact-count discussion, before it
was formalized into the tool description in contracts/tools.md).

Run:
    LLM_BASE_URL=<your ollama endpoint>/v1 \\
    LLM_MODEL=qwen3:8b \\
    uv run --with openai python 02_openai_sdk_ollama_reasoning.py
"""

import os

from openai import OpenAI

BASE_URL = os.environ["LLM_BASE_URL"]
MODEL = os.environ.get("LLM_MODEL", "qwen3:8b")

client = OpenAI(base_url=BASE_URL, api_key="ollama")  # Ollama ignores the key value

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "I want a 2 bedroom apartment in Copacabana, rent between 500 and 950 reais a month."}
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "set_neighborhoods",
                "description": "Set the neighborhood (Bairro) filter to one or more neighborhood names.",
                "parameters": {
                    "type": "object",
                    "properties": {"names": {"type": "array", "items": {"type": "string"}}},
                    "required": ["names"],
                },
            },
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
                        "max": {"type": "number"},
                    },
                    "required": ["field", "min", "max"],
                },
            },
        },
    ],
    tool_choice="auto",
)

message = response.choices[0].message
print("content:", repr(message.content))
print("has reasoning attr:", hasattr(message, "reasoning"))
print("reasoning:", getattr(message, "reasoning", None))
print("model_extra:", message.model_extra)
print("tool_calls:")
for tc in message.tool_calls or []:
    print(" -", tc.function.name, tc.function.arguments)

# Observed result: message.reasoning is populated (a real thinking trace),
# and this run correctly produced all 3 expected tool calls, including
# rooms: {min: 2, max: 2} for "2 bedroom" with no extra prompting.
