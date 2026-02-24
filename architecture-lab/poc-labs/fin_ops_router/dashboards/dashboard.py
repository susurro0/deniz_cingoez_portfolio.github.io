import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import altair as alt

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="FinOps LLM",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# DEFAULT DB PATH (relative to this file)
# --------------------------------------------------
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "telemetry.duckdb"

# --------------------------------------------------
# CSS TUNING
# --------------------------------------------------
st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 0.5rem; }
        h1 { margin-top: 0rem !important; font-size: 1.6rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
        .stDivider { margin: 0.5rem 0 0.8rem 0; }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# LAYOUT
# --------------------------------------------------
filter_col, content_col = st.columns([1, 3])

# --------------------------------------------------
# LEFT COLUMN — FILTERS + DB SELECTOR
# --------------------------------------------------
with filter_col:
    st.subheader("Filters")
    st.caption("Telemetry Source")

    db_path_input = st.text_input(
        "DuckDB file path",
        value=str(DEFAULT_DB_PATH),
        help="Path to telemetry.duckdb"
    )

    DB_PATH = Path(db_path_input).expanduser().resolve()

    if not DB_PATH.exists():
        st.error(f"Database not found:\n{DB_PATH}")
        st.stop()

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data(ttl=60)
def get_data(db_path: Path) -> pd.DataFrame:
    with duckdb.connect(str(db_path), read_only=True) as con:
        df = con.execute(
            "SELECT * FROM telemetry ORDER BY timestamp DESC"
        ).fetchdf()
    return df


raw_df = get_data(DB_PATH)

# --------------------------------------------------
# CLEAN CATEGORICAL DATA TO AVOID ALT WARNING
# --------------------------------------------------
for col in ["model", "strategy", "provider"]:
    raw_df[col] = raw_df[col].fillna("Unknown").replace("empty", "Unknown")

# --------------------------------------------------
# FILTER CONTROLS
# --------------------------------------------------
with filter_col:
    search = st.text_input(
        "Search",
        placeholder="Search Model / Strategy..."
    )

    model_filter = st.multiselect(
        "Model",
        options=sorted(raw_df["model"].unique()),
    )

    strategy_filter = st.multiselect(
        "Strategy",
        options=sorted(raw_df["strategy"].unique()),
    )

    provider_filter = st.multiselect(
        "Provider",
        options=sorted(raw_df["provider"].unique()),
    )

    start_date = st.date_input(
        "Start Date",
        value=raw_df["timestamp"].min().date()
    )

    end_date = st.date_input(
        "End Date",
        value=raw_df["timestamp"].max().date()
    )

    fallback_filter = st.checkbox("Show only fallbacks")
    provider_failed_filter = st.checkbox("Show only provider failures")
    guardrail_filter = st.checkbox("Show only guardrail failures")

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------
df = raw_df.copy()

if search:
    df = df[
        df["strategy"].str.contains(search, case=False) |
        df["model"].str.contains(search, case=False)
    ]

if model_filter:
    df = df[df["model"].isin(model_filter)]

if strategy_filter:
    df = df[df["strategy"].isin(strategy_filter)]

if provider_filter:
    df = df[df["provider"].isin(provider_filter)]

df = df[
    (df["timestamp"].dt.date >= start_date)
    & (df["timestamp"].dt.date <= end_date)
]

if fallback_filter:
    df = df[df["fallback_used"] == True]

if provider_failed_filter:
    df = df[df["provider_failed"] == True]

if guardrail_filter:
    df = df[df["guardrail_failed"] == True]

# --------------------------------------------------
# RIGHT COLUMN — DASHBOARD
# --------------------------------------------------
with content_col:
    st.title("LLM FinOps Dashboard")
    st.caption(f"Active DB: `{DB_PATH.name}`")

    # KPIs
    if not df.empty:
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        c1.metric("Requests", f"{len(df):,}")
        c2.metric("Spend", f"${df['cost_estimated'].sum():.4f}")

        avg_latency = int(df['latency_ms'].mean()) if not df['latency_ms'].isna().all() else 0
        avg_input = int(df['usage_input'].mean()) if not df['usage_input'].isna().all() else 0
        avg_output = int(df['usage_output'].mean()) if not df['usage_output'].isna().all() else 0

        c3.metric("Avg Latency", f"{avg_latency} ms")
        c4.metric("Avg Input", f"{avg_input}")
        c5.metric("Avg Output", f"{avg_output}")
        c6.metric("Fallbacks", f"{df['fallback_used'].sum():,}")
        c7.metric("Provider Failures", f"{df['provider_failed'].sum():,}")
    else:
        st.warning("No data matches your filters.")
        st.stop()

    st.divider()

    # --------------------------------------------------
    # Charts (Altair to avoid warnings)
    # --------------------------------------------------
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.caption("Spend by Model")
        cost_dist = df.groupby("model")["cost_estimated"].sum().reset_index()

        chart1 = alt.Chart(cost_dist).mark_bar().encode(
            x=alt.X('model:N', title="Model"),
            y=alt.Y('cost_estimated:Q', title="Estimated Cost"),
            color=alt.Color('model:N')
        ).properties(height=300)

        st.altair_chart(chart1, use_container_width=True)

        st.caption("Fallbacks & Failures by Strategy")
        fail_chart = df.groupby("strategy")[["fallback_used", "provider_failed"]].sum().reset_index()

        fail_chart_melted = fail_chart.melt(id_vars="strategy", value_vars=["fallback_used", "provider_failed"],
                                            var_name="Type", value_name="Count")

        chart2 = alt.Chart(fail_chart_melted).mark_bar().encode(
            x=alt.X('strategy:N', title="Strategy"),
            y=alt.Y('Count:Q'),
            color=alt.Color('Type:N')
        ).properties(height=300)

        st.altair_chart(chart2, use_container_width=True)

    with col_chart2:
        st.caption("Latency Trend (ms)")
        chart3 = alt.Chart(df).mark_area().encode(
            x=alt.X('timestamp:T', title="Time"),
            y=alt.Y('latency_ms:Q', title="Latency (ms)")
        ).properties(height=300)
        st.altair_chart(chart3, use_container_width=True)

        st.caption("Guardrail Violations Over Time")
        guardrail_df = df[df["guardrail_failed"] == True]
        if not guardrail_df.empty:
            chart4 = alt.Chart(guardrail_df).mark_line().encode(
                x=alt.X('timestamp:T', title="Time"),
                y=alt.Y('guardrail_failed:Q', title="Cumulative Violations", aggregate='sum')
            ).properties(height=300)
            st.altair_chart(chart4, use_container_width=True)
        else:
            st.info("No guardrail violations in selected period.")

    # --------------------------------------------------
    # Full data table
    # --------------------------------------------------
    st.dataframe(
        df,
        height=400,
        width="stretch",
        column_config={
            "cost_estimated": st.column_config.NumberColumn("Cost", format="$%.4f"),
            "timestamp": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"),
            "latency_ms": st.column_config.NumberColumn("Lat", format="%d ms"),
            "guardrail_reason": st.column_config.TextColumn("Guardrail Reason"),
            "guardrail_failed": st.column_config.TextColumn("Guardrail Failed"),
            "fallback_used": st.column_config.TextColumn("Fallback"),
            "provider_failed": st.column_config.TextColumn("Provider Failed"),
        },
        hide_index=True
    )
