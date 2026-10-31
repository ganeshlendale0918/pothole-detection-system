"""
1_Executive_Overview.py — Executive Dashboard for RoadSight Intelligence Platform.
Fixes: KPI rendering via st.metric(), auto-refresh, full analytics layout.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from src.database import (
    get_detections, get_detection_timeline, get_kpi_summary,
    get_locations, get_repair_tasks, init_db,
)
from src.severity import SEVERITY_COLORS
from src.ui_components import (
    empty_state, hero_banner, info_box, inject_css,
    kpi_card, kpi_grid, section_header, severity_pill, status_pill,
)

st.set_page_config(page_title="Executive Overview · RoadSight", page_icon="📊", layout="wide")
init_db()
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>',
        unsafe_allow_html=True,
    )
    model_error = st.session_state.get("model_error")
    if model_error:
        st.markdown('<span class="status-err">⚠ Model unavailable</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-ok">✓ YOLO11n Loaded</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Filters")
    sev_sidebar = st.multiselect(
        "Severity", ["Critical", "High", "Medium", "Low"],
        default=["Critical", "High", "Medium", "Low"],
        key="eo_sev_filter",
    )

# ── Hero ──────────────────────────────────────────────────────────────────────
hero_banner(
    "Executive Overview",
    "Real-time monitoring dashboard — all data from actual detection records",
    "📊",
)

# ── Date filter row ───────────────────────────────────────────────────────────
col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
with col_f1:
    date_from = st.date_input("From", value=date.today() - timedelta(days=30), key="eo_from")
with col_f2:
    date_to = st.date_input("To", value=date.today(), key="eo_to")
with col_f3:
    refresh_interval = st.selectbox("Auto-refresh", ["Off", "30s", "60s", "5min"], key="eo_refresh")
with col_f4:
    st.markdown("<br>", unsafe_allow_html=True)
    manual_refresh = st.button("🔄 Refresh Now", key="eo_manual_refresh")

if manual_refresh:
    st.rerun()

date_from_str = date_from.isoformat()
date_to_str = date_to.isoformat()

# ── Load KPIs ─────────────────────────────────────────────────────────────────
try:
    kpis = get_kpi_summary()
except Exception as e:
    st.error(f"Failed to load KPIs: {e}")
    kpis = {}

dist_sev = kpis.get("severity_distribution", {})
dist_rep = kpis.get("repair_status_distribution", {})

# ── KPI Row 1: Detection KPIs ─────────────────────────────────────────────────
section_header("Detection Overview")
d1, d2, d3, d4, d5, d6 = st.columns(6)
d1.metric("Detections", kpis.get("total_detections", 0), help="Total detection records in database")
d2.metric("Today", kpis.get("today_detections", 0), help="Detections recorded today")
d3.metric("🔴 Critical", dist_sev.get("Critical", 0))
d4.metric("🟠 High", dist_sev.get("High", 0))
d5.metric("🟡 Medium", dist_sev.get("Medium", 0))
d6.metric("🟢 Low", dist_sev.get("Low", 0))

# ── KPI Row 2: Repair KPIs ────────────────────────────────────────────────────
section_header("Repair Overview")
r1, r2, r3, r4, r5, r6 = st.columns(6)
r1.metric("Tasks", kpis.get("total_repair_tasks", 0), help="Total repair tasks created")
r2.metric("Pending Verify", dist_rep.get("Pending Verification", 0))
r3.metric("In Progress", dist_rep.get("In Progress", 0))
r4.metric("Completed", kpis.get("repaired", 0), help="Repaired + Closed tasks")
r5.metric("Completion %", f"{kpis.get('repair_completion_pct', 0)}%")
r6.metric("Est. Cost", f"₹{kpis.get('est_total_cost', 0):,.0f}")

st.markdown("---")

# ── Charts Row 1: Timeline + Severity donut ───────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    section_header("Detection Activity Timeline", "Pothole detections — past 30 days")
    try:
        timeline = get_detection_timeline(days=30)
        if timeline:
            df_tl = pd.DataFrame(timeline)
            fig = px.area(
                df_tl, x="day", y="count",
                color_discrete_sequence=["#4f46e5"],
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c4c4e0",
                xaxis=dict(gridcolor="rgba(255,255,255,0.04)", title=""),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Detections"),
                margin=dict(l=0, r=0, t=10, b=0),
                hovermode="x unified",
            )
            fig.update_traces(
                line_color="#4f46e5",
                fillcolor="rgba(79,70,229,0.12)",
                hovertemplate="%{y} detections<extra></extra>",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("No Detection Data", "Run image or video detection to populate this chart.", "📈")
    except Exception as e:
        st.error(f"Timeline error: {e}")

with col2:
    section_header("Severity Distribution")
    if dist_sev:
        fig_sev = px.pie(
            values=list(dist_sev.values()),
            names=list(dist_sev.keys()),
            color=list(dist_sev.keys()),
            color_discrete_map=SEVERITY_COLORS,
            hole=0.58,
            template="plotly_dark",
        )
        fig_sev.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0",
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        fig_sev.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_sev, use_container_width=True)
    else:
        empty_state("No Severity Data", "Run detections to see distribution.", "🎯")

# ── Charts Row 2: Repair status + Recent activity ─────────────────────────────
col3, col4 = st.columns([1, 2])

STATUS_COLORS = {
    "Pending Verification": "#f59e0b", "Verified": "#3b82f6",
    "Assigned": "#8b5cf6", "In Progress": "#ec4899",
    "Repaired": "#10b981", "Reverified": "#22c55e",
    "Closed": "#4f46e5", "Rejected": "#ef4444",
}

with col3:
    section_header("Repair Status")
    if dist_rep:
        fig_rep = px.bar(
            x=list(dist_rep.values()),
            y=list(dist_rep.keys()),
            orientation="h",
            color=list(dist_rep.keys()),
            color_discrete_map=STATUS_COLORS,
            template="plotly_dark",
        )
        fig_rep.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0", showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)", title="Count"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", title=""),
        )
        st.plotly_chart(fig_rep, use_container_width=True)
    else:
        empty_state("No Repair Tasks", "Create tasks from the Repair Management page.", "🔧")

with col4:
    section_header("Recent Detection Activity")
    try:
        recent = get_detections(limit=12, date_from=date_from_str, date_to=date_to_str)
        if recent:
            for det in recent:
                sev = det.get("severity", "Unknown")
                ts = det.get("created_at", "")[:16].replace("T", " ")
                src = det.get("source_name", "unknown")[:45]
                conf = det.get("confidence", 0)
                pill = severity_pill(sev)
                st.markdown(
                    f'<div class="activity-item">'
                    f'<span class="activity-icon">🔍</span>'
                    f'<span class="activity-text">{pill}&nbsp; '
                    f'<b style="color:#e2e8f0">{src}</b>&nbsp; conf:{conf:.2f}</span>'
                    f'<span class="activity-time">{ts}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            empty_state(
                "No Recent Activity",
                f"No detections between {date_from_str} and {date_to_str}.",
                "🕐",
            )
    except Exception as e:
        st.error(f"Activity error: {e}")

# ── Map mini-preview ──────────────────────────────────────────────────────────
locations = get_locations()
if locations:
    st.markdown("---")
    section_header("Geographic Coverage", "Mapped pothole locations · Open GIS Map for full interaction")
    lmap_col, lstat_col = st.columns([3, 1])
    with lmap_col:
        import folium
        from streamlit_folium import st_folium as _sf
        valid = [l for l in locations if l.get("lat") and l.get("lon") and (abs(float(l["lat"])) > 0.001 or abs(float(l["lon"])) > 0.001)]
        if valid:
            clat = sum(float(l["lat"]) for l in valid) / len(valid)
            clon = sum(float(l["lon"]) for l in valid) / len(valid)
            mini_map = folium.Map(location=[clat, clon], zoom_start=11,
                                  tiles="OpenStreetMap", control_scale=False)
            _FC = {"Critical": "red", "High": "orange", "Medium": "beige", "Low": "green", "Unknown": "gray"}
            for l in valid:
                sev = l.get("severity") or "Unknown"
                folium.CircleMarker(
                    location=[float(l["lat"]), float(l["lon"])],
                    radius=7,
                    color=SEVERITY_COLORS.get(sev, "#94a3b8"),
                    fill=True,
                    fill_opacity=0.8,
                    tooltip=f"{sev}",
                ).add_to(mini_map)
            _sf(mini_map, use_container_width=True, height=280, key="mini_map_eo")
    with lstat_col:
        st.metric("Mapped Potholes", len(valid) if valid else 0)
        st.metric("Unmapped", len(get_detections(limit=500)) - len({l.get("detection_id") for l in locations if l.get("detection_id")}))
        area_list = list({l.get("area_name") for l in locations if l.get("area_name")})
        st.metric("Distinct Areas", len(area_list))

# ── Recent Repair Tasks ───────────────────────────────────────────────────────
st.markdown("---")
section_header("Recent Repair Tasks")
try:
    tasks = get_repair_tasks(limit=10)
    if tasks:
        df_t = pd.DataFrame(tasks)
        show_cols = [c for c in ["id", "status", "priority", "assigned_team", "assigned_worker", "est_cost", "due_date", "updated_at", "severity"] if c in df_t.columns]
        df_show = df_t[show_cols].copy()
        df_show["id"] = df_show["id"].str[:10] + "…"
        if "updated_at" in df_show.columns:
            df_show["updated_at"] = df_show["updated_at"].str[:16].str.replace("T", " ")
        df_show.columns = [c.replace("_", " ").title() for c in df_show.columns]
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        empty_state("No Repair Tasks Yet", "Create tasks from the Repair Management page.", "📋")
except Exception as e:
    st.error(f"Repair tasks error: {e}")

# ── Bottom detection table ────────────────────────────────────────────────────
st.markdown("---")
section_header("Recent Detection Records")
try:
    recent_all = get_detections(limit=20, date_from=date_from_str, date_to=date_to_str)
    if recent_all:
        df_all = pd.DataFrame(recent_all)
        cols_show = [c for c in ["created_at", "source_name", "source_type", "severity", "confidence", "class_name", "conf_threshold"] if c in df_all.columns]
        df_display = df_all[cols_show].copy()
        if "created_at" in df_display.columns:
            df_display["created_at"] = df_display["created_at"].str[:16].str.replace("T", " ")
        df_display.columns = [c.replace("_", " ").title() for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        det_csv = df_all[cols_show].to_csv(index=False).encode()
        st.download_button("⬇️ Export CSV", data=det_csv, file_name="recent_detections.csv", mime="text/csv")
    else:
        empty_state("No detections in selected date range.", "", "🔍")
except Exception as e:
    st.error(f"Recent detections error: {e}")

# ── Auto-refresh ──────────────────────────────────────────────────────────────
_refresh_map = {"30s": 30, "60s": 60, "5min": 300}
_interval = _refresh_map.get(refresh_interval)
if _interval:
    st.caption(f"⏱ Auto-refreshing every {refresh_interval}. Last refresh: {time.strftime('%H:%M:%S')}")
    time.sleep(_interval)
    st.rerun()
