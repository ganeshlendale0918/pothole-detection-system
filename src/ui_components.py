"""
ui_components.py — Reusable Streamlit UI components for RoadSight Intelligence.

All styling uses the global CSS design system injected by inject_css().
KPI cards are rendered using st.columns() with st.metric() rather than raw HTML
to avoid Streamlit's markdown-code-block detection of leading whitespace in HTML.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import streamlit as st

from src.severity import severity_color, severity_badge, SEVERITY_COLORS


# ─────────────────────────────────────────────────────────────────────────────
# CSS Design System
# ─────────────────────────────────────────────────────────────────────────────

GLOBAL_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── App Background ─────────────────────────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #060614 0%, #0b0d1e 40%, #0f0a24 70%, #080d1f 100%) !important;
    min-height: 100vh;
}
.main .block-container {
    padding-top: 1rem !important;
    max-width: 1400px;
}

/* ── Streamlit top toolbar: hide deploy button, darken bar ─────────────── */
header[data-testid="stHeader"] {
    background: rgba(6,6,20,0.97) !important;
    border-bottom: 1px solid rgba(99,102,241,0.15) !important;
    backdrop-filter: blur(10px) !important;
}
[data-testid="stToolbar"] { visibility: hidden !important; }
.stDeployButton { display: none !important; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #09081e 0%, #0e0c2e 60%, #080818 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.2) !important;
}
[data-testid="stSidebar"] .stMarkdown { color: #c4c4e0; }

/* ── Headings ───────────────────────────────────────────────────────────── */
h1, h2, h3 { color: #f1f5f9 !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h4, h5 { color: #cbd5e1 !important; font-weight: 600 !important; }
p, li { color: #94a3b8; }
label { color: #94a3b8 !important; }

/* ── Hero Banner ────────────────────────────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
    border-radius: 16px;
    padding: 1.75rem 2.25rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 20px 60px rgba(79,70,229,0.3);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute; top: -50%; right: -20%; width: 80%; height: 200%;
    background: radial-gradient(ellipse at center, rgba(255,255,255,0.07) 0%, transparent 60%);
    pointer-events: none;
}
.hero-banner h1 { color: white !important; font-size: 1.9rem; font-weight: 800 !important; margin: 0 !important; }
.hero-banner p  { color: rgba(255,255,255,0.85) !important; margin: 0.4rem 0 0 !important; font-size: 0.98rem; }
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.76rem;
    color: white !important;
    font-weight: 600;
    margin-top: 0.65rem;
}

/* ── KPI Native Cards ────────────────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.25rem 1.1rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #db2777);
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(99,102,241,0.22) !important;
    border-color: rgba(99,102,241,0.38) !important;
}
div[data-testid="stMetric"] label {
    color: #7c8ca3 !important;
    font-size: 0.71rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
}
div[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    line-height: 1.15 !important;
}
div[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* ── Custom KPI Cards (HTML-rendered) ────────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
    gap: 0.85rem;
    margin-bottom: 1.25rem;
}
.kpi-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 14px;
    padding: 1.1rem 1.25rem;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(99,102,241,0.2); }
.kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--kpi-accent, linear-gradient(90deg, #6366f1, #8b5cf6));
}
.kpi-icon { font-size: 1.5rem; margin-bottom: 0.4rem; }
.kpi-value { font-size: 1.85rem; font-weight: 800; color: #f1f5f9; line-height: 1; }
.kpi-label { font-size: 0.7rem; color: #64748b; margin-top: 0.3rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
.kpi-sub { font-size: 0.78rem; color: #94a3b8; margin-top: 0.25rem; }

/* ── Glass Cards ─────────────────────────────────────────────────────────── */
.glass-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(99,102,241,0.14);
    border-radius: 14px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(6px);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.glass-card:hover {
    border-color: rgba(99,102,241,0.3);
    box-shadow: 0 8px 24px rgba(99,102,241,0.1);
}
.glass-card-sm {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(99,102,241,0.1);
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.7rem;
}

/* ── Severity Pills ──────────────────────────────────────────────────────── */
.sev-critical { background:#ef444428; color:#f87171; border:1px solid #ef444445; border-radius:18px; padding:2px 10px; font-size:0.76rem; font-weight:700; display:inline-block; }
.sev-high     { background:#f9731628; color:#fb923c; border:1px solid #f9731645; border-radius:18px; padding:2px 10px; font-size:0.76rem; font-weight:700; display:inline-block; }
.sev-medium   { background:#eab30828; color:#fbbf24; border:1px solid #eab30845; border-radius:18px; padding:2px 10px; font-size:0.76rem; font-weight:700; display:inline-block; }
.sev-low      { background:#22c55e28; color:#4ade80; border:1px solid #22c55e45; border-radius:18px; padding:2px 10px; font-size:0.76rem; font-weight:700; display:inline-block; }

/* ── Status Pills ────────────────────────────────────────────────────────── */
.status-ok     { background:#10b98128; color:#34d399; border:1px solid #10b98145; border-radius:18px; padding:2px 10px; font-size:0.78rem; font-weight:600; display:inline-block; }
.status-err    { background:#ef444428; color:#f87171; border:1px solid #ef444445; border-radius:18px; padding:2px 10px; font-size:0.78rem; font-weight:600; display:inline-block; }
.status-warn   { background:#f59e0b28; color:#fbbf24; border:1px solid #f59e0b45; border-radius:18px; padding:2px 10px; font-size:0.78rem; font-weight:600; display:inline-block; }
.status-info   { background:#3b82f628; color:#60a5fa; border:1px solid #3b82f645; border-radius:18px; padding:2px 10px; font-size:0.78rem; font-weight:600; display:inline-block; }
.status-simulated { background:#a855f728; color:#c084fc; border:1px solid #a855f745; border-radius:18px; padding:2px 10px; font-size:0.78rem; font-weight:700; display:inline-block; }

/* ── Info/Warn Boxes ─────────────────────────────────────────────────────── */
.info-box {
    background: rgba(59,130,246,0.07);
    border-left: 3px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.65rem 0;
    color: #93c5fd !important;
    font-size: 0.88rem;
    line-height: 1.6;
}
.warn-box {
    background: rgba(245,158,11,0.07);
    border-left: 3px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.65rem 0;
    color: #fde68a !important;
    font-size: 0.88rem;
    line-height: 1.6;
}
.success-box {
    background: rgba(16,185,129,0.07);
    border-left: 3px solid #10b981;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.65rem 0;
    color: #6ee7b7 !important;
    font-size: 0.88rem;
    line-height: 1.6;
}
.critical-box {
    background: rgba(239,68,68,0.07);
    border-left: 3px solid #ef4444;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.65rem 0;
    color: #fca5a5 !important;
    font-size: 0.88rem;
    line-height: 1.6;
}
.sim-box {
    background: rgba(168,85,247,0.07);
    border: 2px dashed #a855f7;
    border-radius: 8px;
    padding: 0.65rem 1rem;
    margin: 0.5rem 0;
    color: #d8b4fe !important;
    font-size: 0.86rem;
    text-align: center;
    font-weight: 600;
}

/* ── Section Header ──────────────────────────────────────────────────────── */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 1.25rem 0 0.65rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid rgba(99,102,241,0.12);
}
.section-sub { font-size: 0.84rem; color: #64748b; margin-top: -0.45rem; margin-bottom: 0.85rem; }

/* ── Metric Row ──────────────────────────────────────────────────────────── */
.metric-row { display:flex; gap:0.85rem; flex-wrap:wrap; margin-bottom:0.85rem; }
.metric-box {
    background: rgba(99,102,241,0.09);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px;
    padding: 0.8rem 1.25rem;
    flex: 1; min-width: 120px;
    text-align: center;
}
.metric-box .mb-val { font-size: 1.55rem; font-weight: 800; color: #a5b4fc; line-height: 1.1; }
.metric-box .mb-lbl { font-size: 0.69rem; color: #64748b; margin-top: 3px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Timeline ────────────────────────────────────────────────────────────── */
.timeline-item {
    display: flex;
    gap: 0.85rem;
    padding: 0.65rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    align-items: flex-start;
}
.timeline-dot { width: 9px; height: 9px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
.timeline-content { flex: 1; }
.timeline-time { font-size: 0.7rem; color: #475569; font-weight: 500; }
.timeline-text { font-size: 0.83rem; color: #94a3b8; }

/* ── Buttons ─────────────────────────────────────────────────────────────── */
div[data-testid="stButton"] > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    border: none !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 3px 12px rgba(79,70,229,0.28);
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79,70,229,0.4) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 5px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    color: #64748b;
    font-weight: 500;
    font-size: 0.88rem;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(99,102,241,0.1);
    border-bottom: none;
    padding: 0.45rem 0.85rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(99,102,241,0.16) !important;
    color: #a5b4fc !important;
    border-color: rgba(99,102,241,0.3) !important;
}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    border-radius: 7px !important;
    color: #e2e8f0 !important;
}
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(99,102,241,0.18) !important;
    border-radius: 7px !important;
}

/* ── Dataframe ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Expander ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    border-radius: 8px !important;
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}

/* ── Progress bar ────────────────────────────────────────────────────────── */
.stProgress > div > div {
    background: linear-gradient(90deg, #4f46e5, #db2777) !important;
    border-radius: 8px;
}

/* ── Sidebar nav ─────────────────────────────────────────────────────────── */
.nav-section {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569;
    padding: 0.85rem 0 0.35rem;
}
.sidebar-logo {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 1.1rem;
    text-align: center;
}
.sidebar-logo h2 { color: white !important; font-size: 1.1rem; margin: 0 !important; }
.sidebar-logo p  { color: rgba(255,255,255,0.7) !important; font-size: 0.72rem; margin: 2px 0 0 !important; }

/* ── Empty State ─────────────────────────────────────────────────────────── */
.empty-state { text-align: center; padding: 2.5rem 1rem; color: #475569; }
.empty-state .es-icon { font-size: 2.75rem; margin-bottom: 0.85rem; }
.empty-state .es-title { font-size: 1.05rem; font-weight: 600; color: #64748b; margin-bottom: 0.4rem; }
.empty-state .es-sub { font-size: 0.84rem; color: #475569; }

/* ── Activity Feed ───────────────────────────────────────────────────────── */
.activity-item {
    display:flex; align-items:center; gap:0.7rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.035);
}
.activity-icon { font-size: 1rem; flex-shrink:0; }
.activity-text { flex:1; font-size:0.83rem; color:#94a3b8; }
.activity-time { font-size:0.7rem; color:#475569; flex-shrink:0; }

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr { border-color: rgba(99,102,241,0.12) !important; margin: 1rem 0 !important; }

/* ── Streamlit alerts / toasts ───────────────────────────────────────────── */
.stAlert { border-radius: 8px !important; }
div[data-testid="stNotification"] {
    background: rgba(10,10,30,0.95) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
}

/* ── Checkbox / Radio ────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label { color: #94a3b8 !important; }

/* ── Caption / small text ────────────────────────────────────────────────── */
.stCaption, .stCaption p { color: #475569 !important; font-size: 0.78rem !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.5); }
</style>"""


# ─────────────────────────────────────────────────────────────────────────────
# Components
# ─────────────────────────────────────────────────────────────────────────────

def inject_css() -> None:
    """Inject the global CSS design system into the page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def hero_banner(
    title: str,
    subtitle: str,
    icon: str = "🛣️",
    badge: Optional[str] = None,
) -> None:
    badge_html = f'<div class="hero-badge">{badge}</div>' if badge else ""
    html = (
        '<div class="hero-banner">'
        f'<h1>{icon} {title}</h1>'
        f'<p>{subtitle}</p>'
        f'{badge_html}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI cards — rendered via st.metric() to avoid HTML-as-code-block bug
# ─────────────────────────────────────────────────────────────────────────────

def kpi_card(
    value: Any,
    label: str,
    icon: str = "📊",
    sub: str = "",
    accent: str = "linear-gradient(90deg,#6366f1,#8b5cf6)",
) -> str:
    """Return compact HTML for a KPI card (no leading whitespace)."""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card" style="--kpi-accent:{accent}">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'{sub_html}'
        f'</div>'
    )


def kpi_grid(cards: List[str]) -> None:
    """Render a grid of KPI card HTML strings using st.html() for proper rendering."""
    html = '<div class="kpi-grid">' + "".join(cards) + '</div>'
    # Use st.html() in Streamlit ≥1.35, fall back to st.markdown
    try:
        st.html(html)
    except AttributeError:
        st.markdown(html, unsafe_allow_html=True)


def kpi_metrics_row(items: List[Dict[str, Any]]) -> None:
    """
    Render KPI items as native st.metric() widgets in columns.
    items: [{"value": ..., "label": ..., "delta": ..., "icon": ...}, ...]
    """
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            icon = item.get("icon", "")
            label = f"{icon} {item['label']}" if icon else item["label"]
            delta = item.get("delta")
            col.metric(label=label, value=str(item["value"]), delta=delta)


def severity_pill(severity: Optional[str]) -> str:
    """Return inline HTML pill for a severity level."""
    cls_map = {
        "Critical": "sev-critical",
        "High": "sev-high",
        "Medium": "sev-medium",
        "Low": "sev-low",
    }
    cls = cls_map.get(severity or "", "sev-low")
    badge = severity_badge(severity)
    return f'<span class="{cls}">{badge}</span>'


def section_header(title: str, sub: str = "") -> None:
    sub_html = f'<div class="section-sub">{sub}</div>' if sub else ""
    html = f'<div class="section-header">{title}</div>{sub_html}'
    st.markdown(html, unsafe_allow_html=True)


def info_box(msg: str, kind: str = "info") -> None:
    """kind: 'info' | 'warn' | 'success' | 'critical' | 'sim'"""
    cls_map = {
        "info": "info-box", "warn": "warn-box", "success": "success-box",
        "critical": "critical-box", "sim": "sim-box",
    }
    cls = cls_map.get(kind, "info-box")
    html = f'<div class="{cls}">{msg}</div>'
    st.markdown(html, unsafe_allow_html=True)


def empty_state(title: str, sub: str = "", icon: str = "🗂️") -> None:
    html = (
        '<div class="empty-state">'
        f'<div class="es-icon">{icon}</div>'
        f'<div class="es-title">{title}</div>'
        f'<div class="es-sub">{sub}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def metric_row(items: List[Dict[str, Any]]) -> None:
    """items: list of {'val': ..., 'lbl': ...}"""
    boxes = "".join(
        f'<div class="metric-box"><div class="mb-val">{it["val"]}</div>'
        f'<div class="mb-lbl">{it["lbl"]}</div></div>'
        for it in items
    )
    html = f'<div class="metric-row">{boxes}</div>'
    try:
        st.html(html)
    except AttributeError:
        st.markdown(html, unsafe_allow_html=True)


def status_pill(status: str) -> str:
    """Return colour-coded status pill HTML."""
    positive = {"Repaired", "Closed", "Reverified", "Verified"}
    negative = {"Rejected"}
    warning_s = {"Assigned", "In Progress", "Pending Verification"}
    if status in positive:
        cls = "status-ok"
    elif status in negative:
        cls = "status-err"
    elif status in warning_s:
        cls = "status-warn"
    else:
        cls = "status-info"
    return f'<span class="{cls}">{status}</span>'


def simulated_banner() -> None:
    """Show a prominent SIMULATED DATA banner."""
    html = '<div class="sim-box">🔬 SIMULATED DATA — Not from real detections or field records</div>'
    st.markdown(html, unsafe_allow_html=True)


def glass_card(content_html: str, small: bool = False) -> None:
    cls = "glass-card-sm" if small else "glass-card"
    st.markdown(f'<div class="{cls}">{content_html}</div>', unsafe_allow_html=True)


def sidebar_logo() -> None:
    st.sidebar.markdown(
        '<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>',
        unsafe_allow_html=True,
    )


def pagination_controls(
    total: int,
    page_size: int = 50,
    key: str = "page",
) -> int:
    """Display pagination controls and return the current 0-indexed page number."""
    total_pages = max(1, math.ceil(total / page_size))
    if total_pages == 1:
        st.caption(f"{total} record(s) total")
        return 0
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.number_input(
            f"Page (1–{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=key,
        )
    st.caption(f"Page {page} of {total_pages} · {total} records total")
    return int(page) - 1
