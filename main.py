import json

import pandas as pd
import pydeck as pdk
import streamlit as st

import chat

DATA_PATH = "data/dados_apartamentos_with_coordinates.csv"


RANGE_FILTERS = [
    ("Quartos", "Rooms", 1, "%d"),
    ("Vagas", "Parking spots", 1, "%d"),
    ("Suites", "Suites", 1, "%d"),
    ("Area", "Area (m²)", 1, "%d"),
    ("Valor", "Monthly rent (R$)", 50.0, "%.0f"),
    ("Condominio", "Condo fee (R$)", 50.0, "%.0f"),
    ("IPTU", "IPTU (R$)", 50.0, "%.0f"),
]


@st.cache_data
def load_listings():
    return pd.read_csv(DATA_PATH, sep=";")


def neighborhood_filter(df):
    neighborhoods = sorted(df["Bairro"].unique())
    selected = st.sidebar.multiselect("Bairro", options=neighborhoods, key="Bairro")
    if not selected:
        return pd.Series(True, index=df.index)
    return df["Bairro"].isin(selected)


def numeric_range_filter(df, column, label, step, number_format):
    col_min, col_max = df[column].min(), df[column].max()
    if pd.api.types.is_float_dtype(df[column]):
        col_min, col_max = float(col_min), float(col_max)
    else:
        col_min, col_max = int(col_min), int(col_max)

    min_key, max_key = f"{column}_min", f"{column}_max"
    st.session_state.setdefault(min_key, col_min)
    st.session_state.setdefault(max_key, col_max)

    st.sidebar.caption(label)
    left, right = st.sidebar.columns(2)
    selected_min = left.number_input(
        "Min",
        min_value=col_min,
        max_value=col_max,
        step=step,
        format=number_format,
        key=min_key,
    )
    selected_max = right.number_input(
        "Max",
        min_value=col_min,
        max_value=col_max,
        step=step,
        format=number_format,
        key=max_key,
    )
    return df[column].between(selected_min, selected_max)


def render_map(df):
    map_df = df.dropna(subset=["Latitude", "Longitude"])
    if map_df.empty:
        st.info("No listings with map coordinates match the selected filters.")
        return

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["Longitude", "Latitude"],
        get_radius=60,
        radius_min_pixels=1,
        radius_max_pixels=3,
        get_fill_color=[220, 60, 60, 140],
        stroked=True,
        get_line_color=[255, 255, 255, 200],
        line_width_min_pixels=1,
        pickable=True,
    )
    view_state = pdk.data_utils.compute_view(map_df[["Longitude", "Latitude"]])
    tooltip = {
        "html": "<b>{Bairro}</b><br/>"
        "R$ {Valor} / month<br/>"
        "{Quartos} rooms &middot; {Area} m&sup2;",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }
    # deck.gl keeps its own client-side view state and ignores a changed
    # initial_view_state on rerender, so the chart must remount to re-zoom.
    map_key = f"map_{view_state.latitude:.4f}_{view_state.longitude:.4f}_{view_state.zoom}"
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip), key=map_key)


def process_chat_input(df):
    """Mutate session_state from any newly submitted chat message.

    Must run before the filter widgets are instantiated (research.md #4),
    and before the chat history is rendered so the new turn shows up in
    the same run without needing st.rerun().
    """
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    client, model = chat.get_client()
    if client is None:
        st.chat_input(
            "Chat is not configured — set LLM_BASE_URL and LLM_MODEL to enable it.",
            disabled=True,
        )
        return

    user_text = st.chat_input(
        'Describe what you\'re looking for, e.g. "2 bedroom in Copacabana under R$2000"'
    )
    if not user_text:
        return

    st.session_state["chat_history"].append({"role": "user", "content": user_text})
    message = chat.send_chat_message(client, model, user_text)
    if message is None:
        debug = st.session_state.get("last_debug", {})
        reply = f"⚠️ Could not reach the language model backend: {debug.get('error', 'unknown error')}"
    else:
        applied = []
        for tool_call in message.tool_calls or []:
            record = chat.apply_tool_call(tool_call.function.name, tool_call.function.arguments, df)
            if record is not None:
                applied.append(record)
        reply = chat.describe_applied_filters(applied)
    st.session_state["chat_history"].append({"role": "assistant", "content": reply})


def render_chat_panel():
    """Render chat history in a fixed-height scrollable container, plus the
    debug toggle/panel. Call after process_chat_input() so a just-submitted
    turn already appears without an extra rerun.
    """
    st.subheader("Chat")
    with st.container(height=320):
        if not st.session_state["chat_history"]:
            st.caption('Try: "apartments in Copacabana under R$2000".')
        for turn in st.session_state["chat_history"]:
            with st.chat_message(turn["role"]):
                st.write(turn["content"])

    st.checkbox("Show debug info (reasoning + raw tool calls)", key="show_debug")
    if st.session_state["show_debug"]:
        debug = st.session_state.get("last_debug")
        with st.expander("Debug: most recent chat turn", expanded=True):
            if not debug:
                st.caption("No chat turns yet.")
            elif debug.get("error"):
                st.error(debug["error"])
            else:
                st.markdown("**Reasoning**")
                st.write(debug.get("reasoning") or "No reasoning trace provided by this backend.")
                st.markdown("**Raw tool calls**")
                st.code(json.dumps(debug.get("tool_calls_raw", []), indent=2), language="json")


def main():
    st.set_page_config(page_title="Rio Rentals Map", layout="wide")
    st.title("Rio de Janeiro Rental Listings")
    st.caption("Explore rental listings across Rio de Janeiro neighborhoods.")

    df = load_listings()

    if "show_debug" not in st.session_state:
        st.session_state["show_debug"] = False

    process_chat_input(df)

    st.sidebar.header("Filters")
    mask = neighborhood_filter(df)
    for column, label, step, number_format in RANGE_FILTERS:
        mask &= numeric_range_filter(df, column, label, step, number_format)

    filtered_df = df[mask]

    st.caption(f"{len(filtered_df)} of {len(df)} listings match the selected filters.")

    map_col, chat_col = st.columns([2, 1])
    with map_col:
        if filtered_df.empty:
            st.info("No listings match the selected filters.")
        else:
            view = st.segmented_control(
                "View", ["Map", "Table"], default="Map", required=True, label_visibility="collapsed"
            )
            if view == "Table":
                st.dataframe(filtered_df.sort_values("Valor").reset_index(drop=True), height=500)
            else:
                render_map(filtered_df)
    with chat_col:
        render_chat_panel()


if __name__ == "__main__":
    main()
