"""
app.py — RoadSight Intelligence Platform v2.0
Entry point / landing page.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import config
from src.database import get_kpi_summary, init_db
from src.model_loader import get_model, get_model_info, load_model_metadata
from src.ui_components import empty_state, hero_banner, info_box, inject_css, section_header
from src.validation import validate_model_path

# ── Page config (must be the FIRST Streamlit call) ────────────────────────────
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise DB ─────────────────────────────────────────────────────────────
init_db()

# ── Inject global CSS ─────────────────────────────────────────────────────────
inject_css()


# ── Model loading (cached across all pages) ───────────────────────────────────
@st.cache_resource(show_spinner="Loading YOLO11n pothole detection model…")
def load_cached_model():
    metadata = load_model_metadata(config.MODEL_METADATA_PATH)
    model    = get_model(config.DEFAULT_MODEL_PATH)
    info     = get_model_info(model, metadata)
    return model, info, metadata


def try_load_model():
    """Return (model, info, None) or (None, None, error_str)."""
    try:
        validate_model_path(config.DEFAULT_MODEL_PATH)
        model, info, metadata = load_cached_model()
        return model, info, None
    except FileNotFoundError as exc:
        return None, None, str(exc)
    except RuntimeError as exc:
        return None, None, str(exc)
    except Exception as exc:
        return None, None, f"Unexpected error: {exc}"


model, model_info, model_error = try_load_model()

# Share model via session_state so pages can access without reloading
if "model" not in st.session_state:
    st.session_state["model"]       = model
    st.session_state["model_info"]  = model_info
    st.session_state["model_error"] = model_error

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>',
        unsafe_allow_html=True,
    )

    # Model status chip
    if model_error:
        st.markdown('<span class="status-err">⚠ Model unavailable</span>', unsafe_allow_html=True)
        st.caption(model_error[:200])
    else:
        st.markdown('<span class="status-ok">✓ YOLO11n Loaded</span>', unsafe_allow_html=True)
        if model_info:
            st.caption(model_info.get("checkpoint", "models/best.pt"))

    st.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)
    st.page_link("app.py",                                  label="🏠 Home")
    st.page_link("pages/1_Executive_Overview.py",           label="📊 Executive Overview")
    st.page_link("pages/2_Live_Detection.py",               label="🔍 Live Detection")
    st.page_link("pages/3_Detection_History.py",            label="📋 Detection History")
    st.page_link("pages/4_GIS_Map.py",                      label="🗺️ GIS Map")
    st.page_link("pages/5_Road_Condition_Intelligence.py",  label="🛣️ Road Intelligence")
    st.page_link("pages/6_Repair_Management.py",            label="🔧 Repair Management")
    st.page_link("pages/7_Advanced_Analytics.py",           label="📈 Advanced Analytics")
    st.page_link("pages/8_Simulation_Lab.py",               label="🔬 Simulation Lab")
    st.page_link("pages/9_Model_Performance.py",            label="🏆 Model Performance")
    st.page_link("pages/10_Reports_Export.py",              label="📤 Reports & Export")
    st.page_link("pages/11_Settings.py",                    label="⚙️ Settings")

    st.markdown("---")
    st.caption("AI-Based Road Pothole Detection · YOLO11n · v2.0")

# ── Landing Page ──────────────────────────────────────────────────────────────
hero_banner(
    title="RoadSight Intelligence Platform",
    subtitle="AI-powered pothole detection, geospatial analytics, and repair lifecycle management",
    icon="🛣️",
    badge="v2.0 · YOLO11n Custom Checkpoint · Real-time Analysis",
)

# ── Quick KPIs via st.metric() ────────────────────────────────────────────────
try:
    kpis = get_kpi_summary()
except Exception:
    kpis = {}

section_header("Platform Summary")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Detections",    kpis.get("total_detections", 0), help="Total pothole detections in database")
m2.metric("Today",         kpis.get("today_detections", 0), help="Detections recorded today")
m3.metric("High / Critical", kpis.get("high_severity", 0), help="High + Critical severity potholes")
m4.metric("Repair Tasks",  kpis.get("total_repair_tasks", 0), help="Total repair tasks created")
m5.metric("Completion",    f"{kpis.get('repair_completion_pct', 0)}%", help="Repair task completion rate")

st.markdown("---")

# ── Feature cards ─────────────────────────────────────────────────────────────
section_header("Platform Capabilities")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
<div class="glass-card">
<div style="font-size:2rem;margin-bottom:0.6rem">🔍</div>
<strong style="color:#e2e8f0;font-size:0.98rem">Live Detection</strong>
<p style="font-size:0.83rem;margin-top:0.4rem;color:#64748b">
Upload road images or videos for real-time YOLO11n pothole detection
with confidence scores, severity classification, and automatic saving.
</p>
</div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""
<div class="glass-card">
<div style="font-size:2rem;margin-bottom:0.6rem">🗺️</div>
<strong style="color:#e2e8f0;font-size:0.98rem">GIS Mapping</strong>
<p style="font-size:0.83rem;margin-top:0.4rem;color:#64748b">
Pin potholes on an interactive map. Add locations manually, via address
geocoding, or map-click. Visualise density heatmaps and area clusters.
</p>
</div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""
<div class="glass-card">
<div style="font-size:2rem;margin-bottom:0.6rem">🔧</div>
<strong style="color:#e2e8f0;font-size:0.98rem">Repair Management</strong>
<p style="font-size:0.83rem;margin-top:0.4rem;color:#64748b">
Full repair lifecycle with status tracking, team assignment, cost estimation,
before/after images, and overdue alerts. Persisted across restarts.
</p>
</div>""", unsafe_allow_html=True)

c4, c5, c6 = st.columns(3)

with c4:
    st.markdown("""
<div class="glass-card">
<div style="font-size:2rem;margin-bottom:0.6rem">📈</div>
<strong style="color:#e2e8f0;font-size:0.98rem">Advanced Analytics</strong>
<p style="font-size:0.83rem;margin-top:0.4rem;color:#64748b">
Interactive Plotly dashboards: detection trends, severity distributions,
area-wise analysis, repair KPIs, and cost tracking — all from real data.
</p>
</div>""", unsafe_allow_html=True)

with c5:
    st.markdown("""
<div class="glass-card">
<div style="font-size:2rem;margin-bottom:0.6rem">🔬</div>
<strong style="color:#e2e8f0;font-size:0.98rem">Simulation Lab</strong>
<p style="font-size:0.83rem;margin-top:0.4rem;color:#64748b">
Isolated scenario modelling with configurable parameters. Clearly labelled
as simulated — never contaminates real detection history.
</p>
</div>""", unsafe_allow_html=True)

with c6:
    st.markdown("""
<div class="glass-card">
<div style="font-size:2rem;margin-bottom:0.6rem">🏆</div>
<strong style="color:#e2e8f0;font-size:0.98rem">Model Performance</strong>
<p style="font-size:0.83rem;margin-top:0.4rem;color:#64748b">
Verified evaluation metrics from controlled test-set runs. Precision,
Recall, mAP@50, mAP@50-95 — no fabricated numbers.
</p>
</div>""", unsafe_allow_html=True)

st.markdown("---")
info_box(
    "🚀 <b>Get started:</b> Use the sidebar navigation to explore all platform features. "
    "Run <b>Live Detection</b> first to populate the dashboards with real data.",
    kind="info",
)
st.caption(
    "Model: YOLO11n custom checkpoint · Dataset: 665 annotated road images · "
    "Validation mAP@50: 86.97% · All inference runs locally · No data uploaded externally."
)
