"""
7_Advanced_Analytics.py — Interactive Analytics Dashboard for RoadSight.
All charts are derived from actual database records.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from src.database import get_analytics_data, get_detections, get_repair_tasks, init_db
from src.ui_components import inject_css, hero_banner, section_header, empty_state, info_box
from src.severity import SEVERITY_COLORS

st.set_page_config(page_title="Analytics · RoadSight", page_icon="📈", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner("Advanced Analytics", "Interactive charts from real detection and repair records", "📈",
            badge="Plotly · Date Filters · CSV Export")

# ── Date filter ───────────────────────────────────────────────────────────────
fc1, fc2 = st.columns(2)
with fc1:
    af_from = st.date_input("From", value=date.today() - timedelta(days=90), key="aa_from")
with fc2:
    af_to   = st.date_input("To",   value=date.today(),                      key="aa_to")

date_from_s = af_from.isoformat()
date_to_s   = af_to.isoformat()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    analytics = get_analytics_data()
    detections = get_detections(limit=5000, date_from=date_from_s, date_to=date_to_s)
    repair_tasks = get_repair_tasks(limit=2000)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if not detections and not repair_tasks:
    empty_state("No Data Yet", "Run detections and create repair tasks to see analytics.", "📈")
    st.stop()

det_df  = pd.DataFrame(detections)  if detections  else pd.DataFrame()
task_df = pd.DataFrame(repair_tasks) if repair_tasks else pd.DataFrame()

# ── Section: Detection Trends ─────────────────────────────────────────────────
section_header("Detection Trends")

t1, t2 = st.tabs(["📅 Daily", "📊 By Severity"])

with t1:
    if not det_df.empty and "created_at" in det_df.columns:
        det_df["day"] = det_df["created_at"].str[:10]
        daily = det_df.groupby("day").size().reset_index(name="count")
        fig = px.bar(daily, x="day", y="count",
                     title="Daily Detection Count",
                     color_discrete_sequence=["#6366f1"],
                     template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#c4c4e0", xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
        # Export
        csv_d = daily.to_csv(index=False).encode()
        st.download_button("⬇️ Daily CSV", data=csv_d, file_name="daily_detections.csv", mime="text/csv")
    else:
        empty_state("No detection data in date range", "", "📅")

with t2:
    if not det_df.empty and "severity" in det_df.columns and "created_at" in det_df.columns:
        det_df["day"] = det_df["created_at"].str[:10]
        sev_daily = det_df.groupby(["day", "severity"]).size().reset_index(name="count")
        fig2 = px.bar(sev_daily, x="day", y="count", color="severity",
                      barmode="stack",
                      color_discrete_map=SEVERITY_COLORS,
                      title="Daily Detection by Severity",
                      template="plotly_dark")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#c4c4e0", xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        empty_state("No severity-tagged detections", "", "🎯")

st.markdown("---")

# ── Confidence Distribution ───────────────────────────────────────────────────
section_header("Detection Confidence Distribution")
if not det_df.empty and "confidence" in det_df.columns:
    conf_values = analytics.get("confidence_values", det_df["confidence"].tolist())
    fig_conf = px.histogram(
        x=conf_values, nbins=20,
        title="Confidence Score Distribution",
        color_discrete_sequence=["#8b5cf6"],
        template="plotly_dark",
        labels={"x": "Confidence", "y": "Count"},
    )
    fig_conf.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#c4c4e0")
    st.plotly_chart(fig_conf, use_container_width=True)

    # Severity vs Confidence scatter
    fig_sc = px.scatter(
        det_df, x="confidence", y="area_ratio" if "area_ratio" in det_df.columns else "confidence",
        color="severity", color_discrete_map=SEVERITY_COLORS,
        title="Confidence vs Area Ratio (coloured by Severity)",
        template="plotly_dark",
        hover_data=["source_name"] if "source_name" in det_df.columns else [],
    )
    fig_sc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#c4c4e0")
    st.plotly_chart(fig_sc, use_container_width=True)
else:
    empty_state("No confidence data", "", "📊")

st.markdown("---")

# ── Area-wise Analysis ────────────────────────────────────────────────────────
section_header("Area-wise Detection Analysis")
area_dist = analytics.get("area_distribution", [])
if area_dist:
    df_area = pd.DataFrame(area_dist).head(15)
    fig_area = px.bar(df_area, x="count", y="area_name", orientation="h",
                      title="Potholes by Area (Top 15)",
                      color="count",
                      color_continuous_scale=["#6366f1", "#ec4899"],
                      template="plotly_dark")
    fig_area.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#c4c4e0", coloraxis_showscale=False)
    st.plotly_chart(fig_area, use_container_width=True)
else:
    empty_state("No area data", "Add area names via the GIS Map.", "🗺️")

st.markdown("---")

# ── Repair Analytics ──────────────────────────────────────────────────────────
section_header("Repair & Maintenance Analytics")
if not task_df.empty:
    rc1, rc2 = st.columns(2)

    with rc1:
        # Status distribution donut
        if "status" in task_df.columns:
            STATUS_COLORS = {
                "Pending Verification": "#f59e0b", "Verified": "#3b82f6",
                "Assigned": "#8b5cf6", "In Progress": "#ec4899",
                "Repaired": "#10b981", "Reverified": "#22c55e",
                "Closed": "#6366f1", "Rejected": "#ef4444",
            }
            s_dist = task_df["status"].value_counts().reset_index()
            s_dist.columns = ["status", "count"]
            fig_s = px.pie(s_dist, values="count", names="status",
                           color="status", color_discrete_map=STATUS_COLORS,
                           hole=0.55, title="Repair Status Distribution",
                           template="plotly_dark")
            fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                                margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_s, use_container_width=True)

    with rc2:
        # Priority distribution
        if "priority" in task_df.columns:
            PRIO_COLORS = {"Critical": "#ef4444", "High": "#f97316",
                           "Medium": "#eab308", "Low": "#22c55e"}
            p_dist = task_df["priority"].value_counts().reset_index()
            p_dist.columns = ["priority", "count"]
            fig_p = px.bar(p_dist, x="priority", y="count",
                           color="priority", color_discrete_map=PRIO_COLORS,
                           title="Repair Tasks by Priority",
                           template="plotly_dark")
            fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#c4c4e0", showlegend=False)
            st.plotly_chart(fig_p, use_container_width=True)

    # Cost analysis
    if "est_cost" in task_df.columns:
        cost_df = task_df[task_df["est_cost"].notna()].copy()
        if not cost_df.empty:
            section_header("Cost Analysis")
            fig_cost = px.scatter(
                cost_df, x="est_cost",
                y="actual_cost" if "actual_cost" in cost_df.columns else "est_cost",
                color="priority" if "priority" in cost_df.columns else None,
                color_discrete_map={"Critical":"#ef4444","High":"#f97316","Medium":"#eab308","Low":"#22c55e"},
                title="Estimated vs Actual Repair Cost (₹)",
                template="plotly_dark",
                labels={"est_cost": "Estimated Cost (₹)", "actual_cost": "Actual Cost (₹)"},
            )
            fig_cost.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#c4c4e0")
            st.plotly_chart(fig_cost, use_container_width=True)

    task_csv = task_df.to_csv(index=False).encode()
    st.download_button("⬇️ Download Repair Tasks CSV", data=task_csv,
                       file_name="repair_tasks_analytics.csv", mime="text/csv")
else:
    empty_state("No Repair Tasks", "Create tasks from the Repair Management page.", "🔧")

# ── Excel export ──────────────────────────────────────────────────────────────
st.markdown("---")
section_header("Export All Analytics Data")
if not det_df.empty or not task_df.empty:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if not det_df.empty:
            det_df.to_excel(writer, sheet_name="Detections", index=False)
        if not task_df.empty:
            task_df.to_excel(writer, sheet_name="Repair Tasks", index=False)
    buf.seek(0)
    st.download_button("⬇️ Download All Data (Excel)", data=buf.getvalue(),
                       file_name="roadsight_analytics.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
