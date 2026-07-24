import os
from typing import Literal

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()

FilterField = Literal[
    "rooms", "parking_spots", "suites", "area",
    "monthly_rent", "condo_fee", "iptu",
]

FIELD_TO_COLUMN = {
    "rooms": "Quartos",
    "parking_spots": "Vagas",
    "suites": "Suites",
    "area": "Area",
    "monthly_rent": "Valor",
    "condo_fee": "Condominio",
    "iptu": "IPTU",
}

FIELD_LABELS = {
    "rooms": "rooms",
    "parking_spots": "parking spots",
    "suites": "suites",
    "area": "area",
    "monthly_rent": "monthly rent",
    "condo_fee": "condo fee",
    "iptu": "IPTU",
}


class SetNeighborhoodsArgs(BaseModel):
    names: list[str]


class SetNumericRangeArgs(BaseModel):
    field: FilterField
    min: float
    max: float


class ResetFiltersArgs(BaseModel):
    pass


ARG_MODELS = {
    "set_neighborhoods": SetNeighborhoodsArgs,
    "set_numeric_range": SetNumericRangeArgs,
    "reset_filters": ResetFiltersArgs,
}

TOOL_DESCRIPTIONS = {
    "set_neighborhoods": "Set the neighborhood (Bairro) filter to one or more neighborhood names.",
    "set_numeric_range": (
        "Set a min/max range filter for one numeric listing field. "
        'For an exact value (e.g. "2 bedrooms"), set min and max to the same number.'
    ),
    "reset_filters": "Clear all filters currently set (via chat or manually) back to their defaults, showing every listing again.",
}


def _tool_schema(name, model):
    schema = model.model_json_schema()
    schema.pop("title", None)
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": TOOL_DESCRIPTIONS[name],
            "parameters": schema,
        },
    }


TOOLS = [_tool_schema(name, model) for name, model in ARG_MODELS.items()]


def get_client():
    base_url = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_MODEL")
    if not base_url or not model:
        return None, None
    api_key = os.environ.get("LLM_API_KEY", "placeholder")

    # If the backend sits behind Cloudflare Access (e.g. the ollama-homelab
    # tunnel), a service token's two headers must ride along on every call.
    cf_client_id = os.environ.get("CF_ACCESS_CLIENT_ID")
    cf_client_secret = os.environ.get("CF_ACCESS_CLIENT_SECRET")
    default_headers = None
    if cf_client_id and cf_client_secret:
        default_headers = {
            "CF-Access-Client-Id": cf_client_id,
            "CF-Access-Client-Secret": cf_client_secret,
        }

    return OpenAI(base_url=base_url, api_key=api_key, default_headers=default_headers), model


def send_chat_message(client, model, user_text):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_text}],
            tools=TOOLS,
            tool_choice="auto",
        )
    except Exception as exc:
        st.session_state["last_debug"] = {"reasoning": None, "tool_calls_raw": [], "error": str(exc)}
        return None

    if not hasattr(response, "choices"):
        # A non-JSON response (e.g. an HTML page from an auth gate blocking
        # the request) isn't raised as an error by the OpenAI SDK — it's
        # returned as a plain string instead. Treat it as a backend failure.
        snippet = str(response)[:200]
        st.session_state["last_debug"] = {
            "reasoning": None,
            "tool_calls_raw": [],
            "error": f"Backend returned a non-API response, likely blocked upstream: {snippet!r}",
        }
        return None

    message = response.choices[0].message
    st.session_state["last_debug"] = {
        "reasoning": getattr(message, "reasoning", None),
        "tool_calls_raw": [
            {"name": tc.function.name, "arguments": tc.function.arguments}
            for tc in (message.tool_calls or [])
        ],
        "error": None,
    }
    return message


def apply_tool_call(tool_name, raw_arguments, df):
    model_cls = ARG_MODELS.get(tool_name)
    if model_cls is None:
        return None
    try:
        args = model_cls.model_validate_json(raw_arguments)
    except ValidationError:
        return None

    if tool_name == "set_neighborhoods":
        known = set(df["Bairro"].unique())
        recognized = [name for name in args.names if name in known]
        unrecognized = [name for name in args.names if name not in known]
        st.session_state["Bairro"] = recognized
        return {"tool": "set_neighborhoods", "names": recognized, "unrecognized": unrecognized}

    if tool_name == "set_numeric_range":
        column = FIELD_TO_COLUMN[args.field]
        col_min, col_max = df[column].min(), df[column].max()
        clamped_min = max(args.min, col_min)
        clamped_max = min(args.max, col_max)
        if pd.api.types.is_float_dtype(df[column]):
            clamped_min, clamped_max = float(clamped_min), float(clamped_max)
        else:
            clamped_min, clamped_max = int(clamped_min), int(clamped_max)
        st.session_state[f"{column}_min"] = clamped_min
        st.session_state[f"{column}_max"] = clamped_max
        return {"tool": "set_numeric_range", "field": args.field, "min": clamped_min, "max": clamped_max}

    if tool_name == "reset_filters":
        st.session_state.pop("Bairro", None)
        for column in FIELD_TO_COLUMN.values():
            st.session_state.pop(f"{column}_min", None)
            st.session_state.pop(f"{column}_max", None)
        return {"tool": "reset_filters"}

    return None


def describe_applied_filters(applied):
    if not applied:
        return (
            "I couldn't find any matching filters in that message. "
            "Try naming a neighborhood, a price range, number of rooms, etc."
        )

    parts = []
    unrecognized_all = []
    for record in applied:
        if record["tool"] == "set_neighborhoods":
            if record["names"]:
                parts.append(f"neighborhood set to {', '.join(record['names'])}")
            unrecognized_all.extend(record.get("unrecognized", []))
        elif record["tool"] == "set_numeric_range":
            label = FIELD_LABELS.get(record["field"], record["field"])
            parts.append(f"{label} between {record['min']:g} and {record['max']:g}")
        elif record["tool"] == "reset_filters":
            parts.append("all filters reset")

    if parts:
        message = "Applied: " + "; ".join(parts) + "."
    else:
        message = "I couldn't find any matching filters in that message."
    if unrecognized_all:
        message += f" (Didn't recognize: {', '.join(unrecognized_all)}.)"
    return message
