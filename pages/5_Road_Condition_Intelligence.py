"""
5_Road_Condition_Intelligence.py — Road Condition Analysis & Risk Scoring.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from src.database import get_detections, get_locations, get_repair_tasks, init_db
from src.risk_score import compute_area_risk_scores, _risk_label
from src.ui_components import inject_css, hero_banner, section_header, info_box, empty_state, kpi_card, kpi_grid
from src.severity import SEVERITY_COLORS

st.set_page_config(page_title="Road Intelligence · RoadSight", page_icon="🛣️", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner("Road Condition Intelligence",
            "Area-wise risk scoring, detection density, and temporal patterns — from actual records",
            "🛣️", badge="Transparent Risk Formula · No Fabricated Data")

info_box(
    "📖 <b>Risk Score Formula:</b> R = 0.30×(density) + 0.30×(avg severity) + "
    "0.20×(recurrence) + 0.20×(age of unresolved records). "
    "Scores are normalised 0–100. Weights are configurable in Settings.",
    kind="info",
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    detections  = get_detections(limit=2000)
    locations   = get_locations()
    repair_tasks = get_repair_tasks(limit=1000)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if not detections and not locations:
    empty_state("No Data Available",
                "Run detections and add locations to see Road Condition Intelligence.", "🛣️")
    st.stop()

# Merge locations with detections
loc_df = pd.DataFrame(locations) if locations else pd.DataFrame()
det_df = pd.DataFrame(detections) if detections else pd.DataFrame()

# Enrich detections with area_name from locations
if not loc_df.empty and "detection_id" in loc_df.columns and not det_df.empty:
    area_map = dict(zip(loc_df["detection_id"].dropna(), loc_df["area_name"].fillna("Unknown")))
    det_df["area_name"] = det_df["id"].map(area_map).fillna(det_df["source_name"].apply(lambda x: x[:30] if x else "Unknown"))
else:
    if not det_df.empty:
        det_df["area_name"] = det_df.get("source_name", pd.Series(["Unknown"] * len(det_df))).apply(lambda x: str(x)[:30])

# ── Risk Scores ───────────────────────────────────────────────────────────────
section_header("Area Risk Scores")
risk_data = compute_area_risk_scores(
    det_df.to_dict("records") if not det_df.empty else [],
    repair_tasks,
    w_count=config.RISK_W_COUNT,
    w_severity=config.RISK_W_SEVERITY,
    w_recurrence=config.RISK_W_RECURRENCE,
    w_age=config.RISK_W_AGE,
)

if risk_data:
    df_risk = pd.DataFrame(risk_data)
    rc1, rc2 = st.columns([2, 1])
    with rc1:
        fig_risk = px.bar(
            df_risk.head(15),
            x="risk_score", y="area_name",
            orientation="h",
            color="risk_score",
            color_continuous_scale=["#22c55e", "#eab308", "#f97316", "#ef4444"],
            title="Top 15 High-Risk Areas",
            template="plotly_dark",
            labels={"risk_score": "Risk Score (0-100)", "area_name": ""},
        )
        fig_risk.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0", margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    with rc2:
        st.markdown("**Risk Score Table**")
        df_risk_show = df_risk[["area_name", "pothole_count", "avg_severity", "risk_score", "risk_label"]].copy()
        df_risk_show.columns = ["Area", "Count", "Avg Sev", "Score", "Label"]
        st.dataframe(df_risk_show, use_container_width=True, hide_index=True)
else:
    empty_state("No area data", "Add area names via the GIS Map.", "🗺️")

# ── Severity by area ──────────────────────────────────────────────────────────
st.markdown("---")
if not det_df.empty and "severity" in det_df.columns and "area_name" in det_df.columns:
    section_header("Severity Distribution by Area")
    area_sev = (
        det_df.groupby(["area_name", "severity"])
        .size()
        .reset_index(name="count")
    )
    if not area_sev.empty:
        top_areas = det_df["area_name"].value_counts().head(10).index.tolist()
        area_sev_top = area_sev[area_sev["area_name"].isin(top_areas)]
        fig_as = px.bar(
            area_sev_top, x="area_name", y="count",
            color="severity", barmode="stack",
            color_discrete_map=SEVERITY_COLORS,
            title="Pothole Severity by Area (Top 10)",
            template="plotly_dark",
        )
        fig_as.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0", xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_as, use_container_width=True)

# ── Temporal patterns ─────────────────────────────────────────────────────────
st.markdown("---")
section_header("Detection Patterns Over Time")
if not det_df.empty and "created_at" in det_df.columns:
    det_df["day"] = det_df["created_at"].str[:10]
    det_df["week"] = pd.to_datetime(det_df["created_at"].str[:10], errors="coerce").dt.to_period("W").astype(str)

    daily = det_df.groupby("day").size().reset_index(name="count")
    if not daily.empty:
        fig_d = px.line(daily, x="day", y="count",
                        title="Daily Detection Count",
                        color_discrete_sequence=["#6366f1"],
                        template="plotly_dark",
                        markers=True)
        fig_d.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0",
        )
        st.plotly_chart(fig_d, use_container_width=True)

# ── High-risk ranking ─────────────────────────────────────────────────────────
st.markdown("---")
section_header("High-Risk Location Rankings")
if not det_df.empty:
    hri = det_df[det_df["severity"].isin(["Critical", "High"])].copy() if "severity" in det_df.columns else det_df.copy()
    if not hri.empty and "area_name" in hri.columns:
        rank = hri.groupby("area_name").agg(
            count=("id", "count"),
            avg_conf=("confidence", "mean"),
        ).reset_index().sort_values("count", ascending=False).head(10)
        rank.columns = ["Area", "High/Critical Potholes", "Avg Confidence"]
        rank["Avg Confidence"] = rank["Avg Confidence"].round(3)
        st.dataframe(rank, use_container_width=True, hide_index=True)
    else:
        info_box("No High/Critical detections in current records.", kind="warn")

# ── Download ──────────────────────────────────────────────────────────────────
if risk_data:
    risk_csv = pd.DataFrame(risk_data).to_csv(index=False).encode()
    st.download_button("⬇️ Download Risk Scores CSV", data=risk_csv,
                       file_name="area_risk_scores.csv", mime="text/csv")
