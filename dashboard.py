"""Run with:  streamlit run dashboard.py"""
import sqlite3
from contextlib import closing

import pandas as pd
import streamlit as st

import config

st.set_page_config(page_title="RAG cost & latency dashboard", layout="wide")
st.title("RAG platform: cost, cache and latency")

with closing(sqlite3.connect(config.METRICS_DB)) as conn:
    df = pd.read_sql("SELECT * FROM requests ORDER BY id", conn)
if df.empty:
    st.info("No requests logged yet. Run `python run_compare.py` or call /ask first.")
    st.stop()

runs = sorted(df.run_label.unique())
chosen = st.multiselect("Runs to show", runs, default=runs)
df = df[df.run_label.isin(chosen)]

summary = df.groupby("run_label").agg(
    requests=("id", "count"),
    cache_hit_rate=("cache_hit", "mean"),
    cost_per_request=("cost_usd", "mean"),
    total_cost=("cost_usd", "sum"),
    p50_latency_s=("latency_ms", lambda s: s.quantile(0.5) / 1000),
    p95_latency_s=("latency_ms", lambda s: s.quantile(0.95) / 1000),
    quality=("correct", "mean"),
).round(5)
st.subheader("Summary per run")
st.dataframe(summary, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Cumulative cost")
    cum = pd.DataFrame({
        label: g.cost_usd.cumsum().reset_index(drop=True) for label, g in df.groupby("run_label")
    })
    st.line_chart(cum)
with c2:
    st.subheader("Route split")
    route = df.assign(route=df.route.fillna("cache hit")).groupby(["run_label", "route"]).size().unstack(fill_value=0)
    st.bar_chart(route)

c3, c4 = st.columns(2)
with c3:
    st.subheader("Latency per request (s)")
    lat = pd.DataFrame({
        label: (g.latency_ms / 1000).reset_index(drop=True) for label, g in df.groupby("run_label")
    })
    st.line_chart(lat)
with c4:
    st.subheader("Answer quality by route")
    q = df.dropna(subset=["correct"]).assign(route=lambda d: d.route.fillna("cache hit"))
    if q.empty:
        st.caption("Quality is only recorded in compare runs.")
    else:
        st.bar_chart(q.groupby(["run_label", "route"]).correct.mean().unstack())
