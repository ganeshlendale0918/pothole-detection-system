"""
3_Detection_History.py — Paginated detection history with filters.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta

import pandas as pd
import streamlit as st
import plotly.express as px

import config
from src.database import get_detections, count_detections, delete_detection, init_db
from src.ui_components import inject_css, hero_banner, section_header, info_box, empty_state, severity_pill, pagination_controls
from src.severity import SEVERITY_COLORS

st.set_page_config(page_title="Detection History · RoadSight", page_icon="📋", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner("Detection History", "Browse and manage all saved pothole detections", "📋")

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔍 Filter & Search", expanded=True):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        date_from = st.date_input("From", value=date.today() - timedelta(days=90), key="dh_from")
    with fc2:
        date_to   = st.date_input("To",   value=date.today(),                      key="dh_to")
    with fc3:
        sev_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low", "Unknown"], key="dh_sev")
    with fc4:
        src_filter = st.selectbox("Source type", ["All", "image", "video", "demo"], key="dh_src")

    search = st.text_input("Search by filename or notes", key="dh_search", placeholder="e.g. road_photo.jpg")

date_from_s = date_from.isoformat()
date_to_s   = date_to.isoformat()
sev_q   = None if sev_filter == "All" else sev_filter
src_q   = None if src_filter == "All" else src_filter
search_q = search.strip() or None

PAGE_SIZE = 50
total = count_detections(severity=sev_q, source_type=src_q,
                         date_from=date_from_s, date_to=date_to_s)

st.markdown(f"**{total}** detection(s) match the current filters.")

if total == 0:
    empty_state("No Detections Found",
                "Run Live Detection to populate the history, or adjust the filters.", "🕳️")
    st.stop()

# Pagination
page_idx = pagination_controls(total, PAGE_SIZE, key="dh_page")

rows = get_detections(
    limit=PAGE_SIZE, offset=page_idx * PAGE_SIZE,
    severity=sev_q, source_type=src_q,
    date_from=date_from_s, date_to=date_to_s,
    search=search_q,
)

# ── Table ─────────────────────────────────────────────────────────────────────
section_header("Detection Records")
df = pd.DataFrame(rows)
if df.empty:
    empty_state("No records on this page.", "", "📋")
else:
    display_cols = ["id", "created_at", "source_name", "source_type",
                    "severity", "confidence", "class_name",
                    "image_width", "image_height", "conf_threshold"]
    avail = [c for c in display_cols if c in df.columns]
    df_show = df[avail].copy()
    df_show["id"] = df_show["id"].str[:8] + "…"
    df_show["created_at"] = df_show["created_at"].str[:16].str.replace("T", " ")
    df_show.columns = [c.replace("_", " ").title() for c in df_show.columns]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # Download this page
    csv_bytes = df[avail].to_csv(index=False).encode()
    st.download_button("⬇️ Download this page as CSV", data=csv_bytes,
                       file_name="detections_page.csv", mime="text/csv")

# ── Charts ────────────────────────────────────────────────────────────────────
if not df.empty and "severity" in df.columns:
    st.markdown("---")
    ch1, ch2 = st.columns(2)
    with ch1:
        section_header("Severity Distribution (Current Page)")
        sev_counts = df["severity"].value_counts().reset_index()
        sev_counts.columns = ["severity", "count"]
        fig = px.pie(sev_counts, values="count", names="severity",
                     color="severity", color_discrete_map=SEVERITY_COLORS,
                     hole=0.5, template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                          margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        section_header("Confidence Distribution (Current Page)")
        if "confidence" in df.columns:
            fig2 = px.histogram(df, x="confidence", nbins=15,
                                color_discrete_sequence=["#6366f1"],
                                template="plotly_dark")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#c4c4e0", margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

# ── Delete record ─────────────────────────────────────────────────────────────
st.markdown("---")
section_header("Delete a Record")
info_box("⚠️ Deletion is permanent and cannot be undone.", kind="warn")
del_id = st.text_input("Enter full Detection ID to delete:", key="dh_del_id", placeholder="UUID")
if st.button("🗑️ Delete", key="dh_del_btn"):
    if del_id.strip():
        try:
            delete_detection(del_id.strip())
            st.success(f"✅ Detection {del_id[:8]}… deleted.")
            st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}")
    else:
        st.warning("Enter a detection ID to delete.")
