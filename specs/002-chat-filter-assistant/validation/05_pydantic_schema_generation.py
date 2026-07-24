"""Validation step 5 — after deciding against the full PydanticAI `Agent`
framework (see validation/04's finding), confirm the middle ground works:
declaring each tool's arguments as a plain `pydantic.BaseModel`,
auto-generating its JSON schema for the `tools=[...]` request, and
validating the model's returned arguments back against that same model.

Used for: the reworked research.md #1/#3, contracts/tools.md, and
data-model.md — this is the actual design those now document.

Run:
    uv run --with openai,pydantic python 05_pydantic_schema_generation.py
"""

import json
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, ValidationError


class SetNeighborhoodsArgs(BaseModel):
    names: list[str]


class SetNumericRangeArgs(BaseModel):
    field: Literal["rooms", "parking_spots", "suites", "area", "monthly_rent", "condo_fee", "iptu"]
    min: float
    max: float


class ResetFiltersArgs(BaseModel):
    pass


def tool_schema(name: str, description: str, model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)  # cosmetic only; harmless either way
    return {
        "type": "function",
        "function": {"name": name, "description": description, "parameters": schema},
    }


TOOLS = [
    tool_schema(
        "set_neighborhoods",
        "Set the neighborhood (Bairro) filter to one or more neighborhood names.",
        SetNeighborhoodsArgs,
    ),
    tool_schema(
        "set_numeric_range",
        'Set a min/max range filter for one numeric listing field. For an exact value (e.g. "2 bedrooms"), set min and max to the same number.',
        SetNumericRangeArgs,
    ),
    tool_schema(
        "reset_filters",
        "Clear all filters back to their defaults, showing every listing again.",
        ResetFiltersArgs,
    ),
]

ARG_MODELS = {
    "set_neighborhoods": SetNeighborhoodsArgs,
    "set_numeric_range": SetNumericRangeArgs,
    "reset_filters": ResetFiltersArgs,
}

print("=== generated tool schemas (from BaseModel.model_json_schema()) ===")
print(json.dumps(TOOLS, indent=2))
print()

client = OpenAI(base_url="https://ollama.interfacesdigitais.com.br/v1", api_key="ollama")
response = client.chat.completions.create(
    model="qwen3:8b",
    messages=[
        {"role": "user", "content": "I want a 2 bedroom apartment in Copacabana, rent between 500 and 950 reais a month."}
    ],
    tools=TOOLS,
    tool_choice="auto",
)

print("=== tool_calls parsed + validated via Pydantic ===")
for tc in (response.choices[0].message.tool_calls or []):
    model_cls = ARG_MODELS[tc.function.name]
    try:
        parsed = model_cls.model_validate_json(tc.function.arguments)
        print(f" - {tc.function.name}: OK ->", parsed)
    except ValidationError as e:
        print(f" - {tc.function.name}: VALIDATION ERROR ->", e)

# Observed result: Ollama accepts the Pydantic-generated schema (the extra
# per-property "title" fields Pydantic adds are ignored, as expected for
# any JSON Schema consumer), and model_validate_json() successfully parses
# the returned tool-call arguments into typed, validated objects. This is
# the design now written into contracts/tools.md and data-model.md: a
# BaseModel per tool is the single source of truth for both the schema
# sent to the model and the validation applied to its response -- with no
# full agent/tool-execution-loop framework involved.
