import streamlit as st
import duckdb
import pandas as pd

DB_PATH = "telemetry.duckdb"

st.set_page_config(
    page_title="FinOps LLM",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SAFE CSS (keeps theme + avoids clipping) ---
st.markdown("""
<style>
    /* Slightly reduce padding but keep title visible */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }

    /* Keep title readable and not clipped */
    h1 {
        margin-top: 0.2rem !important;
        font-size: 1.8rem !important;
    }

    /* Compact metrics without touching theme colors */
    [data-testid="stMetricValue"] {
        font-size: 20px !important;
    }

    .stDivider {
        margin: 0.4rem 0 0.8rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_data():
    with duckdb.connect(DB_PATH, read_only=True) as con:
        stats = con.execute("""
            SELECT 
                COUNT(*) as total_req,
                AVG(latency_ms) as avg_lat,
                SUM(cost_estimated) as total_cost,
                AVG(input_tokens) as avg_in,
                AVG(output_tokens) as avg_out
            FROM telemetry
        """).fetchone()
        df = con.execute("SELECT * FROM telemetry ORDER BY timestamp DESC").fetchdf()
    return df, stats

df, stats = get_data()

# --- HEADER ---
st.title("LLM FinOps Dashboard")

# --- KPIs ---
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Requests", f"{stats[0]:,}")
c2.metric("Total Spend", f"${stats[2]:.4f}")
c3.metric("Avg Latency", f"{int(stats[1])}ms")
c4.metric("Avg Input", f"{int(stats[3])}")
c5.metric("Avg Output", f"{int(stats[4])}")

st.divider()

# --- CHARTS ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.caption("Spend by Model")
    cost_dist = df.groupby("model")["cost_estimated"].sum().reset_index()

    st.bar_chart(
        cost_dist,
        x="model",
        y="cost_estimated",
        color="model",
        height=300,      # <-- 160 is too small for grouped bars
        width="stretch"
    )


with col_chart2:
    st.caption("Latency Trend (ms)")
    st.area_chart(
        df.set_index("timestamp")["latency_ms"],
        height=300,
        width="stretch")

# --- TABLE ---
st.subheader("Recent Activity")

search = st.text_input(
    "Filter Strategy/Model",
    label_visibility="collapsed",
    placeholder="Filter by Model or Strategy..."
)

if search:
    display_df = df[
        df['strategy'].str.contains(search, case=False) |
        df['model'].str.contains(search, case=False)
    ]
else:
    display_df = df

# Height tuned to fit 1080p screens without scrolling
TABLE_HEIGHT = 360

st.dataframe(
    display_df,
    height=TABLE_HEIGHT,
    width="stretch",
    column_config={
        "cost_estimated": st.column_config.NumberColumn("Cost", format="$%.4f"),
        "timestamp": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"),
        "latency_ms": st.column_config.NumberColumn("Lat", format="%dms"),
    },
    hide_index=True
)
