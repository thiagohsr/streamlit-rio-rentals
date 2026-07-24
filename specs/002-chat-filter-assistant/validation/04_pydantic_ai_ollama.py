"""Validation step 4 — evaluate switching from the raw `openai` SDK
(validation 02/03) to the full PydanticAI `Agent` + `@agent.tool` framework,
prompted by discussing future persona support (a renter/buyer assistant vs.
a pricing/profit advisor for professionals).

Used for: deciding whether to rework research.md/contracts/tools.md/
tasks.md around PydanticAI for the CURRENT chat-filter-assistant feature.

Run:
    uv run --with pydantic-ai python 04_pydantic_ai_ollama.py
(base_url is hardcoded below to the confirmed Ollama endpoint used
throughout this feature's research; no secret is needed for Ollama.)
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

FilterField = Literal["rooms", "parking_spots", "suites", "area", "monthly_rent", "condo_fee", "iptu"]


@dataclass
class ChatDeps:
    applied: list = field(default_factory=list)


model = OpenAIChatModel(
    "qwen3:8b",
    provider=OpenAIProvider(base_url="https://ollama.interfacesdigitais.com.br/v1", api_key="ollama"),
)
agent = Agent(model, deps_type=ChatDeps)


@agent.tool
def set_neighborhoods(ctx: RunContext[ChatDeps], names: list[str]) -> str:
    """Set the neighborhood (Bairro) filter to one or more neighborhood names."""
    ctx.deps.applied.append(("set_neighborhoods", names))
    return f"neighborhoods set to {names}"


@agent.tool
def set_numeric_range(ctx: RunContext[ChatDeps], field: FilterField, min: float, max: float) -> str:
    """Set a min/max range filter for one numeric listing field.

    For an exact value (e.g. "2 bedrooms"), set min and max to the same number.
    """
    ctx.deps.applied.append(("set_numeric_range", field, min, max))
    return f"{field} range set to {min}-{max}"


deps = ChatDeps()
result = agent.run_sync(
    "I want a 2 bedroom apartment in Copacabana, rent between 500 and 950 reais a month.",
    deps=deps,
)

print("=== output (final model text — NOT what we'd show the user; see finding below) ===")
print(repr(result.output))
print()
print("=== deps.applied (our own deterministic record, same pattern as apply_tool_call) ===")
print(deps.applied)
print()
print("=== usage ===")
print(result.usage)

# Observed result (with proper tool docstrings + Literal field type this
# time, a fair comparison to validation 02/03's raw-SDK test):
#
#   RunUsage(input_tokens=855, output_tokens=1797, requests=2, tool_calls=2)
#
# Two key findings that changed the recommendation:
#
# 1. PydanticAI's Agent.run() makes 2 model requests per turn by design:
#    one to decide+execute tool calls, a second to synthesize final text
#    from the tool results (visible as result.output). Our design doesn't
#    need that second call at all -- we already generate the user-facing
#    confirmation deterministically from executed tool calls (research.md
#    #3), exactly like `deps.applied` here. So adopting Agent.run() as-is
#    means paying for a synthesis call whose output we'd discard.
#
# 2. On this run, the *second* call's reasoning trace (ThinkingPart) is
#    ~1500 tokens of the model re-deliberating whether it should have
#    called set_numeric_range for "rooms" too, going back and forth, and
#    ultimately NOT calling it -- so the final tool_calls count (2) still
#    missed the rooms filter, same gap as validation 01, despite proper
#    docstrings this time. Meanwhile validation 02's single raw-SDK call
#    got all 3 tool calls right, in one request, with a much shorter
#    reasoning trace. This isn't proof PydanticAI is "worse" (LLM outputs
#    are stochastic; single-call runs have also missed tools before -- see
#    validation 01), but it does confirm the structural cost: 2x requests
#    and substantially more tokens for a synthesis step we don't need,
#    with no demonstrated accuracy benefit in this test.
#
# Conclusion carried into research.md: keep the raw `openai` SDK + a plain
# Pydantic model (not the full Agent/tool-loop) for this feature's
# single-persona, state-mutating tool calls. Revisit full PydanticAI
# Agents specifically if/when a future advisor persona needs genuine
# structured *synthesized* output (e.g. a pricing recommendation) rather
# than direct UI-state tool calls -- that's the case its 2-call design is
# actually built for.
