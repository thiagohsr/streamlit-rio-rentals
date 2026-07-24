"""Validation step 3 — confirm the same `openai` SDK code path works
unchanged against OpenRouter (the documented alternative backend), and
check what happens to the `reasoning` field access on a model that doesn't
provide one.

Used for: research.md #1 (one client library covers both backends via
base_url swap) and #2 (the debug view must handle "reasoning attribute
present but empty", not just "attribute missing").

Never hardcode the API key here — export it as an env var before running.

Run:
    LLM_API_KEY=<your openrouter key> \\
    LLM_MODEL=openai/gpt-4o-mini \\
    uv run --with openai python 03_openai_sdk_openrouter.py
"""

import os

from openai import OpenAI

API_KEY = os.environ["LLM_API_KEY"]
MODEL = os.environ.get("LLM_MODEL", "openai/gpt-4o-mini")

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

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
print("tool_calls:")
for tc in message.tool_calls or []:
    print(" -", tc.function.name, tc.function.arguments)

# Observed result: all 3 expected tool calls came back correctly (same as
# Ollama), but message.reasoning is present as an attribute and is `None`
# — gpt-4o-mini doesn't expose a reasoning trace via this API. Confirms the
# debug view (FR-010) must handle both "no attribute" and "attribute is
# None/empty" cases, not assume reasoning is always available.
