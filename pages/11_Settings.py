"""
11_Settings.py — Platform Settings for RoadSight Intelligence Platform.

Persistent key-value settings stored in the app_settings table.
Includes inference defaults, display preferences, map defaults, and risk weights.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

import config
from src.database import get_setting, set_setting, init_db, get_kpi_summary
from src.ui_components import (
    inject_css, hero_banner, section_header, info_box,
    empty_state, kpi_card, kpi_grid,
)

st.set_page_config(page_title="Settings · RoadSight", page_icon="⚙️", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner(
    "Platform Settings",
    "Configure inference defaults, display preferences, and risk scoring parameters",
    "⚙️",
    badge="Persistent · SQLite-backed · No Code Changes Required",
)

info_box(
    "All settings are stored in the application database and persist across restarts. "
    "Changes take effect on the next page load / rerun. "
    "Defaults are sourced from <b>config.py</b>.",
    kind="info",
)

# ─────────────────────────────────────────────────────────────────────────────
# Load current persistent settings (fall back to config.py defaults)
# ─────────────────────────────────────────────────────────────────────────────
def _gs(key: str, default):
    return get_setting(key, default)


tabs = st.tabs([
    "🔍 Inference",
    "🗺️ Map",
    "⚖️ Risk Scoring",
    "🎨 Display",
    "🗃️ Data Management",
    "ℹ️ About",
])

# ████████████████████████████████████████████████████████████████████████████
# TAB: Inference
# ████████████████████████████████████████████████████████████████████████████
with tabs[0]:
    section_header("Inference Settings", "Defaults applied to the Live Detection page")
    st.markdown("""
    <div class="glass-card-sm">
        <b style="color:#a5b4fc">Note:</b>
        <span style="color:#94a3b8"> These are default values shown in the detection UI sliders.
        The operator can override them per-session on the Live Detection page.
        Changing them here does NOT retrain or modify the model.</span>
    </div>
    """, unsafe_allow_html=True)

    ic1, ic2 = st.columns(2)
    with ic1:
        conf_default = st.slider(
            "Default Confidence Threshold",
            min_value=0.1, max_value=0.95, step=0.01,
            value=float(_gs("conf_threshold", config.DEFAULT_CONF)),
            help="Detections below this confidence are discarded.",
            key="sett_conf",
        )
        iou_default = st.slider(
            "Default IoU (NMS) Threshold",
            min_value=0.1, max_value=0.95, step=0.01,
            value=float(_gs("iou_threshold", config.DEFAULT_IOU)),
            help="IoU threshold for Non-Maximum Suppression.",
            key="sett_iou",
        )
    with ic2:
        imgsz_default = st.selectbox(
            "Default Inference Image Size",
            [416, 512, 640, 800, 1024],
            index=[416, 512, 640, 800, 1024].index(
                int(_gs("imgsz", config.DEFAULT_IMGSZ))
            ) if int(_gs("imgsz", config.DEFAULT_IMGSZ)) in [416, 512, 640, 800, 1024] else 3,
            help="Inference resolution. Higher = slower but potentially more accurate.",
            key="sett_imgsz",
        )
        max_frames = st.slider(
            "Max Frames per Video",
            min_value=50, max_value=1000, step=50,
            value=int(_gs("max_video_frames", config.MAX_VIDEO_FRAMES)),
            help="Limit frame extraction for large video files to avoid memory issues.",
            key="sett_maxframes",
        )

    if st.button("💾 Save Inference Settings", key="save_inf"):
        try:
            set_setting("conf_threshold",   conf_default)
            set_setting("iou_threshold",    iou_default)
            set_setting("imgsz",            imgsz_default)
            set_setting("max_video_frames", max_frames)
            st.success("✅ Inference settings saved.")
        except Exception as e:
            st.error(f"Save failed: {e}")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Map
# ████████████████████████████████████████████████████████████████████████████
with tabs[1]:
    section_header("Map Settings", "Default GIS map centre and zoom level")

    mc1, mc2 = st.columns(2)
    with mc1:
        map_lat = st.number_input(
            "Default Latitude",
            min_value=-90.0, max_value=90.0, step=0.1,
            value=float(_gs("map_default_lat", config.DEFAULT_MAP_LAT)),
            key="sett_map_lat",
        )
        map_lon = st.number_input(
            "Default Longitude",
            min_value=-180.0, max_value=180.0, step=0.1,
            value=float(_gs("map_default_lon", config.DEFAULT_MAP_LON)),
            key="sett_map_lon",
        )
    with mc2:
        map_zoom = st.slider(
            "Default Zoom Level",
            min_value=2, max_value=18, step=1,
            value=int(_gs("map_default_zoom", config.DEFAULT_MAP_ZOOM)),
            key="sett_map_zoom",
        )
        geocoding_enabled = st.checkbox(
            "Enable Address Geocoding (requires internet)",
            value=bool(_gs("geocoding_enabled", True)),
            key="sett_geocoding",
            help="Uses the Nominatim/geopy service. Disable for offline use.",
        )

    info_box(
        "Map defaults set here are used as the initial view when opening the GIS Map page. "
        "Current default centre is India (neutral starting point).",
        kind="info",
    )

    if st.button("💾 Save Map Settings", key="save_map"):
        try:
            set_setting("map_default_lat",  map_lat)
            set_setting("map_default_lon",  map_lon)
            set_setting("map_default_zoom", map_zoom)
            set_setting("geocoding_enabled", geocoding_enabled)
            st.success("✅ Map settings saved.")
        except Exception as e:
            st.error(f"Save failed: {e}")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Risk Scoring
# ████████████████████████████████████████████████████████████████████████████
with tabs[2]:
    section_header("Risk Score Weights",
                   "Configure the Road Condition Intelligence risk scoring formula")

    info_box(
        "Risk Score = w₁·norm(count) + w₂·norm(severity) + w₃·norm(recurrence) + w₄·norm(age_days). "
        "Weights do not need to sum to exactly 1.0 — they are normalised internally. "
        "<b>This is a prioritisation aid, not a validated safety prediction.</b>",
        kind="warn",
    )

    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        w_count = st.slider("Count Weight",      0.0, 1.0, float(_gs("risk_w_count",      config.RISK_W_COUNT)),      0.05, key="rw_count")
    with rc2:
        w_sev   = st.slider("Severity Weight",   0.0, 1.0, float(_gs("risk_w_severity",   config.RISK_W_SEVERITY)),   0.05, key="rw_sev")
    with rc3:
        w_recur = st.slider("Recurrence Weight", 0.0, 1.0, float(_gs("risk_w_recurrence", config.RISK_W_RECURRENCE)), 0.05, key="rw_recur")
    with rc4:
        w_age   = st.slider("Age Weight",        0.0, 1.0, float(_gs("risk_w_age",        config.RISK_W_AGE)),        0.05, key="rw_age")

    total_w = w_count + w_sev + w_recur + w_age
    st.markdown(f"**Sum of weights:** `{total_w:.2f}` {'✅' if abs(total_w - 1.0) < 0.05 else '⚠️'}")
    if abs(total_w - 1.0) > 0.05:
        st.caption("Weights are normalised internally, so the sum doesn't need to be exactly 1.0.")

    severity_thresholds = st.columns(3)
    with severity_thresholds[0]:
        t_critical = st.number_input("Critical Threshold (area ratio)",
                                      min_value=0.0, max_value=1.0, step=0.01,
                                      value=float(_gs("sev_thresh_critical", config.SEVERITY_THRESHOLD_CRITICAL)),
                                      key="sett_t_crit")
    with severity_thresholds[1]:
        t_high = st.number_input("High Threshold",
                                   min_value=0.0, max_value=1.0, step=0.01,
                                   value=float(_gs("sev_thresh_high", config.SEVERITY_THRESHOLD_HIGH)),
                                   key="sett_t_high")
    with severity_thresholds[2]:
        t_medium = st.number_input("Medium Threshold",
                                    min_value=0.0, max_value=1.0, step=0.01,
                                    value=float(_gs("sev_thresh_medium", config.SEVERITY_THRESHOLD_MEDIUM)),
                                    key="sett_t_med")

    if st.button("💾 Save Risk Settings", key="save_risk"):
        try:
            set_setting("risk_w_count",      w_count)
            set_setting("risk_w_severity",   w_sev)
            set_setting("risk_w_recurrence", w_recur)
            set_setting("risk_w_age",        w_age)
            set_setting("sev_thresh_critical", t_critical)
            set_setting("sev_thresh_high",     t_high)
            set_setting("sev_thresh_medium",   t_medium)
            st.success("✅ Risk scoring settings saved.")
        except Exception as e:
            st.error(f"Save failed: {e}")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Display
# ████████████████████████████████████████████████████████████████████████████
with tabs[3]:
    section_header("Display & Notification Settings")

    dc1, dc2 = st.columns(2)
    with dc1:
        refresh_interval = st.slider(
            "Dashboard auto-refresh interval (seconds)",
            min_value=10, max_value=300, step=10,
            value=int(_gs("refresh_interval", 30)),
            help="Used when 'Auto-refresh' is enabled on the Executive Overview.",
            key="sett_refresh",
        )
        page_size = st.slider(
            "Records per page",
            min_value=10, max_value=200, step=10,
            value=int(_gs("page_size", config.PAGE_SIZE)),
            key="sett_pagesize",
        )
    with dc2:
        cost_currency = st.selectbox(
            "Cost Currency Symbol",
            ["₹", "USD ($)", "EUR (€)", "GBP (£)", "Custom"],
            index=["₹", "USD ($)", "EUR (€)", "GBP (£)", "Custom"].index(
                str(_gs("cost_currency", "₹"))
            ) if str(_gs("cost_currency", "₹")) in ["₹", "USD ($)", "EUR (€)", "GBP (£)", "Custom"] else 0,
            key="sett_currency",
        )
        show_confidence = st.checkbox(
            "Show confidence scores on detection history",
            value=bool(_gs("show_confidence", True)),
            key="sett_showconf",
        )

    if st.button("💾 Save Display Settings", key="save_disp"):
        try:
            set_setting("refresh_interval", refresh_interval)
            set_setting("page_size",        page_size)
            set_setting("cost_currency",    cost_currency)
            set_setting("show_confidence",  show_confidence)
            st.success("✅ Display settings saved.")
        except Exception as e:
            st.error(f"Save failed: {e}")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Data Management
# ████████████████████████████████████████████████████████████████████████████
with tabs[4]:
    section_header("Data Management", "Database statistics and maintenance")

    try:
        kpis = get_kpi_summary()
        dm_cards = [
            kpi_card(kpis.get("total_detections", 0),  "Total Detections",  "🔍",
                     accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
            kpi_card(kpis.get("total_repair_tasks", 0),"Repair Tasks",      "🔧",
                     accent="linear-gradient(90deg,#ec4899,#a855f7)"),
            kpi_card(config.DB_PATH.stat().st_size // 1024 if config.DB_PATH.is_file() else "N/A",
                     "Database Size (KB)", "🗄️",
                     accent="linear-gradient(90deg,#10b981,#22c55e)"),
        ]
        kpi_grid(dm_cards)
    except Exception as e:
        st.error(f"Could not load stats: {e}")

    st.markdown("---")
    section_header("Database Path")
    st.code(str(config.DB_PATH))

    section_header("Upload Directory")
    st.code(str(config.UPLOAD_DIR))

    section_header("Model Checkpoint")
    st.code(str(config.DEFAULT_MODEL_PATH))
    if config.DEFAULT_MODEL_PATH.is_file():
        sz_mb = config.DEFAULT_MODEL_PATH.stat().st_size / 1_048_576
        st.caption(f"✅ Found — {sz_mb:.1f} MB")
    else:
        st.warning("⚠️ Model file not found at configured path.")

    st.markdown("---")
    info_box(
        "⚠️ <b>No deletion controls are provided here</b> to prevent accidental data loss. "
        "To clear specific records, use the Detection History or GIS Map pages. "
        "To reset the entire database, delete the SQLite file at the path above and restart the application.",
        kind="warn",
    )


# ████████████████████████████████████████████████████████████████████████████
# TAB: About
# ████████████████████████████████████████████████████████████████████████████
with tabs[5]:
    section_header("About RoadSight Intelligence Platform")
    st.markdown("""
    <div class="glass-card">
        <h3 style="color:#a5b4fc;margin-bottom:1rem">🛣️ RoadSight Intelligence Platform v2.0</h3>
        <p>An advanced AI-powered road monitoring system for pothole detection, geospatial
        analysis, repair lifecycle management, and road condition intelligence.</p>

        <h4 style="color:#c4c4e0;margin:1.5rem 0 0.75rem">Core Technologies</h4>
        <ul>
            <li>🤖 <b>YOLO11n</b> — Custom-trained pothole detection model (Ultralytics)</li>
            <li>🗺️ <b>Folium / streamlit-folium</b> — Interactive GIS mapping</li>
            <li>📊 <b>Plotly</b> — Interactive analytics and visualisations</li>
            <li>🗄️ <b>SQLite (WAL mode)</b> — Persistent local database</li>
            <li>📤 <b>openpyxl / fpdf2</b> — Export and reporting</li>
            <li>🌍 <b>geopy / Nominatim</b> — Address geocoding (optional)</li>
        </ul>

        <h4 style="color:#c4c4e0;margin:1.5rem 0 0.75rem">Model Info</h4>
        <ul>
            <li>Checkpoint: <code>models/best.pt</code></li>
            <li>Architecture: YOLO11n (Nano)</li>
            <li>Dataset: 665 annotated road images</li>
            <li>Test mAP@50: 78.05%</li>
            <li>Test Precision: 84.96%</li>
            <li>Inference: ~12 ms/image</li>
        </ul>

        <h4 style="color:#c4c4e0;margin:1.5rem 0 0.75rem">Non-Negotiable Design Rules</h4>
        <ul>
            <li>✅ Model weights are never modified or retrained automatically</li>
            <li>✅ All evaluation metrics sourced from real evaluation files</li>
            <li>✅ Simulated data is strictly isolated in dedicated tables</li>
            <li>✅ GPS/location data is never fabricated</li>
            <li>✅ All records persist across application restarts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="glass-card-sm" style="margin-top:1rem">
        <p style="font-size:0.8rem;color:#475569">
            Database: <code>{config.DB_PATH}</code><br>
            Model: <code>{config.DEFAULT_MODEL_PATH}</code><br>
            Version: 2.0.0 · Platform Upgrade Complete
        </p>
    </div>
    """, unsafe_allow_html=True)
