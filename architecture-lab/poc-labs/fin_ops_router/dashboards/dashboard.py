import streamlit as st
import duckdb
import pandas as pd

DB_PATH = "telemetry.duckdb"

st.set_page_config(page_title="FinOps LLM", layout="wide", initial_sidebar_state="collapsed")

# --- CSS TUNING ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 0.5rem; }
    h1 { margin-top: 0rem !important; font-size: 1.6rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    .stDivider { margin: 0.5rem 0 0.8rem 0; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=60)
def get_data():
    with duckdb.connect(DB_PATH, read_only=True) as con:
        df = con.execute("SELECT * FROM telemetry ORDER BY timestamp DESC").fetchdf()
    return df

raw_df = get_data()

# --- LAYOUT: FILTERS LEFT, CONTENT RIGHT ---
filter_col, content_col = st.columns([1, 3])

# -----------------------------
# LEFT COLUMN — FILTER PANEL
# -----------------------------
with filter_col:
    st.subheader("Filters")

    # Global search
    search = st.text_input(
        "Search",
        placeholder="Search Model/Strategy..."
    )

    # Structured filters
    model_filter = st.multiselect(
        "Model",
        options=sorted(raw_df["model"].unique()),
        default=None
    )

    strategy_filter = st.multiselect(
        "Strategy",
        options=sorted(raw_df["strategy"].unique()),
        default=None
    )

    provider_filter = st.multiselect(
        "Provider",
        options=sorted(raw_df["provider"].unique()),
        default=None
    )

    # Date range
    start_date = st.date_input(
        "Start Date",
        value=raw_df["timestamp"].min().date()
    )
    end_date = st.date_input(
        "End Date",
        value=raw_df["timestamp"].max().date()
    )

# -----------------------------
# APPLY FILTERS
# -----------------------------
df = raw_df.copy()

# Global text search
if search:
    df = df[
        df["strategy"].str.contains(search, case=False) |
        df["model"].str.contains(search, case=False)
    ]

# Model filter
if model_filter:
    df = df[df["model"].isin(model_filter)]

# Strategy filter
if strategy_filter:
    df = df[df["strategy"].isin(strategy_filter)]

# Provider filter
if provider_filter:
    df = df[df["provider"].isin(provider_filter)]

# Date range filter
df = df[
    (df["timestamp"].dt.date >= start_date) &
    (df["timestamp"].dt.date <= end_date)
]

# -----------------------------
# RIGHT COLUMN — DASHBOARD
# -----------------------------
with content_col:

    # HEADER
    st.title("LLM FinOps Dashboard")

    # KPIs
    if not df.empty:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Requests", f"{len(df):,}")
        c2.metric("Spend", f"${df['cost_estimated'].sum():.4f}")
        c3.metric("Avg Latency", f"{int(df['latency_ms'].mean())}ms")
        c4.metric("Avg Input", f"{int(df['input_tokens'].mean())}")
        c5.metric("Avg Output", f"{int(df['output_tokens'].mean())}")
    else:
        st.warning("No data matches your filter.")

    st.divider()

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.caption("Spend by Model")
        cost_dist = df.groupby("model")["cost_estimated"].sum().reset_index()
        st.bar_chart(
            cost_dist,
            x="model",
            y="cost_estimated",
            color="model",
            height=300,
            width="stretch"
        )

    with col_chart2:
        st.caption("Latency Trend (ms)")
        st.area_chart(
            df.set_index("timestamp")["latency_ms"],
            height=300,
            width="stretch"
        )

    st.dataframe(
        df,
        height=400,
        width="stretch",
        column_config={
            "cost_estimated": st.column_config.NumberColumn("Cost", format="$%.4f"),
            "timestamp": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"),
            "latency_ms": st.column_config.NumberColumn("Lat", format="%dms"),
        },
        hide_index=True
    )