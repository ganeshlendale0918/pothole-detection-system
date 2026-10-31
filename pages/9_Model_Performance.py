"""
9_Model_Performance.py — Model Evaluation Center for RoadSight Intelligence Platform.

Displays actual evaluation metrics from research_reports/results/ files.
No metrics are fabricated. Uses the real YOLO11n checkpoint evaluation results.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from src.database import get_detections, init_db
from src.ui_components import (
    inject_css, hero_banner, section_header, info_box,
    empty_state, kpi_card, kpi_grid, metric_row,
)

st.set_page_config(page_title="Model Performance · RoadSight", page_icon="🏆", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner(
    "Model Performance Center",
    "Verified evaluation metrics from the YOLO11n custom pothole-detection checkpoint",
    "🏆",
    badge="YOLO11n · 665 Images · Real Evaluation Data",
)

info_box(
    "All metrics shown here are sourced directly from evaluation CSV/JSON files in "
    "<b>research_reports/results/</b>. No numbers are fabricated. "
    "Validation metrics come from the held-out validation set (66 images); "
    "test metrics from the independent test set (67 images).",
    kind="info",
)

# ─────────────────────────────────────────────────────────────────────────────
# Load evaluation data from disk
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def load_comparison_json() -> dict:
    p = config.FINAL_COMPARISON_JSON
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


@st.cache_data(ttl=600, show_spinner=False)
def load_comparison_csv() -> pd.DataFrame:
    p = config.FINAL_COMPARISON_CSV
    if p.is_file():
        try:
            return pd.read_csv(p)
        except Exception:
            pass
    return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_experiment_csv() -> pd.DataFrame:
    p = config.EXPERIMENT_RESULTS_CSV
    if p.is_file():
        try:
            return pd.read_csv(p)
        except Exception:
            pass
    return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_training_audit() -> pd.DataFrame:
    p = config.TRAINING_AUDIT_CSV
    if p.is_file():
        try:
            return pd.read_csv(p)
        except Exception:
            pass
    return pd.DataFrame()


# Load all available data
cmp_json   = load_comparison_json()
cmp_df     = load_comparison_csv()
exp_df     = load_experiment_csv()
train_df   = load_training_audit()

# ─────────────────────────────────────────────────────────────────────────────
# Main model metrics (YOLO11n — our primary model)
# ─────────────────────────────────────────────────────────────────────────────
models_data = cmp_json.get("models", [])
yolo11n = next((m for m in models_data if "YOLO11n" in m.get("Model", "")), None)
yolov8n = next((m for m in models_data if "YOLOv8n" in m.get("Model", "")), None)
detr    = next((m for m in models_data if "DETR"    in m.get("Model", "")), None)

# ── Section: Primary Model KPIs ────────────────────────────────────────────
section_header("Primary Model: YOLO11n Custom Checkpoint", "Test-set evaluation results — real data")

if yolo11n:
    prec   = yolo11n.get("Precision", 0)
    rec    = yolo11n.get("Recall",    0)
    map50  = yolo11n.get("mAP50",     0)
    map95  = yolo11n.get("mAP50-95",  0)
    inf_ms = yolo11n.get("Inference (ms)", 0) or 0
    f1_val = 2 * prec * rec / max(prec + rec, 1e-9)
    fps    = round(1000 / inf_ms, 1) if inf_ms and inf_ms > 0 else None

    cards = [
        kpi_card(f"{prec*100:.1f}%",   "Precision",       "🎯", accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
        kpi_card(f"{rec*100:.1f}%",    "Recall",           "📡", accent="linear-gradient(90deg,#8b5cf6,#ec4899)"),
        kpi_card(f"{f1_val*100:.1f}%", "F1 Score",         "⚖️", accent="linear-gradient(90deg,#ec4899,#f97316)"),
        kpi_card(f"{map50*100:.1f}%",  "mAP@50",           "🏆", accent="linear-gradient(90deg,#f97316,#eab308)"),
        kpi_card(f"{map95*100:.1f}%",  "mAP@50-95",        "📊", accent="linear-gradient(90deg,#eab308,#22c55e)"),
        kpi_card(f"{inf_ms:.1f}ms",    "Inference Time",   "⚡", accent="linear-gradient(90deg,#22c55e,#10b981)"),
        kpi_card(f"{fps or '—'}",      "Estimated FPS",    "🎞️", accent="linear-gradient(90deg,#10b981,#3b82f6)"),
        kpi_card(f"{yolo11n.get('Test Images', 67)}",  "Test Images",   "🖼️", accent="linear-gradient(90deg,#3b82f6,#6366f1)"),
    ]
    kpi_grid(cards)

    info_box(
        f"YOLO11n achieves <b>mAP@50 = {map50*100:.1f}%</b> and "
        f"<b>Precision = {prec*100:.1f}%</b> on the 67-image independent test set. "
        f"Inference time: {inf_ms:.1f} ms/image. "
        "These are results from controlled test-set evaluation — not operational field metrics.",
        kind="success",
    )
else:
    info_box("Primary model evaluation data not found in research_reports/results/.", kind="warn")

# ── Section: Model Comparison ────────────────────────────────────────────────
st.markdown("---")
section_header("Model Comparison", "YOLO11n vs YOLOv8n vs DETR-R50 on the same test set")

if not cmp_df.empty:
    numeric_cols = ["Precision", "Recall", "mAP50", "mAP50-95", "F1"]
    # Convert percentage values to 0–100 if they appear to be fractions
    for col in ["Precision", "Recall", "mAP50", "mAP50-95"]:
        if col in cmp_df.columns:
            # If values look like fractions (< 1.5), multiply by 100
            if cmp_df[col].max() < 1.5:
                cmp_df[col] = cmp_df[col] * 100

    display_cols = [c for c in ["Model", "Precision", "Recall", "mAP50", "mAP50-95", "F1", "Inference (ms)"]
                    if c in cmp_df.columns]
    st.dataframe(cmp_df[display_cols].set_index("Model") if "Model" in cmp_df.columns else cmp_df,
                 use_container_width=True)

    # Radar chart comparison
    radar_metrics = ["Precision", "Recall", "mAP50", "mAP50-95"]
    radar_available = [m for m in radar_metrics if m in cmp_df.columns]

    if len(radar_available) >= 3 and "Model" in cmp_df.columns:
        section_header("Radar: Multi-Metric Comparison")
        fig_radar = go.Figure()
        color_seq = ["#6366f1", "#ec4899", "#10b981"]
        for idx, (_, row) in enumerate(cmp_df.iterrows()):
            vals = [row.get(m, 0) for m in radar_available]
            vals_closed = vals + [vals[0]]
            cats_closed = radar_available + [radar_available[0]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_closed, theta=cats_closed,
                fill="toself",
                name=row.get("Model", f"Model {idx}"),
                line=dict(color=color_seq[idx % len(color_seq)]),
                fillcolor=color_seq[idx % len(color_seq)].replace(")", ",0.12)").replace("rgb", "rgba") if "rgb" in color_seq[idx % len(color_seq)] else color_seq[idx % len(color_seq)] + "20",
            ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            title="Model Comparison Radar Chart",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # Bar chart comparison
    section_header("Bar Chart: Key Metrics")
    chart_metrics = [m for m in ["Precision", "Recall", "mAP50", "mAP50-95"] if m in cmp_df.columns]
    if chart_metrics and "Model" in cmp_df.columns:
        df_melt = cmp_df.melt(id_vars=["Model"], value_vars=chart_metrics,
                               var_name="Metric", value_name="Score (%)")
        fig_bar = px.bar(df_melt, x="Metric", y="Score (%)", color="Model",
                         barmode="group", template="plotly_dark",
                         color_discrete_sequence=["#6366f1", "#ec4899", "#10b981"],
                         title="Performance Metrics by Model",
                         range_y=[0, 100])
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#c4c4e0",
                               legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Download
    dl_csv = cmp_df.to_csv(index=False).encode()
    st.download_button("⬇️ Download Comparison CSV", data=dl_csv,
                       file_name="model_comparison.csv", mime="text/csv")
else:
    empty_state("Comparison Data Not Found", "Place final_model_comparison.csv in research_reports/results/", "📊")

# ── Section: Dataset Statistics ──────────────────────────────────────────────
st.markdown("---")
section_header("Dataset Statistics", "Information about the training and evaluation dataset")

ds_cards = [
    kpi_card(config.DATASET_TOTAL_IMAGES, "Total Images",      "🖼️", accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
    kpi_card(config.DATASET_TRAIN,        "Training Images",   "📚", accent="linear-gradient(90deg,#8b5cf6,#ec4899)"),
    kpi_card(config.DATASET_VAL,          "Validation Images", "✅", accent="linear-gradient(90deg,#10b981,#22c55e)"),
    kpi_card(config.DATASET_TEST,         "Test Images",       "🔬", accent="linear-gradient(90deg,#3b82f6,#6366f1)"),
    kpi_card("1",                          "Classes",           "🎯", accent="linear-gradient(90deg,#f59e0b,#fbbf24)"),
    kpi_card("Pascal VOC → YOLO",          "Annotation Format","📝", accent="linear-gradient(90deg,#ec4899,#a855f7)"),
]
kpi_grid(ds_cards)

ds_col1, ds_col2 = st.columns(2)
with ds_col1:
    split_data = {"Train": config.DATASET_TRAIN, "Val": config.DATASET_VAL, "Test": config.DATASET_TEST}
    fig_split = px.pie(values=list(split_data.values()), names=list(split_data.keys()),
                       color_discrete_sequence=["#6366f1", "#10b981", "#ec4899"],
                       hole=0.5, template="plotly_dark", title="Dataset Split")
    fig_split.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                             margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_split, use_container_width=True)

with ds_col2:
    st.markdown("""
    <div class="glass-card">
        <div style="color:#a5b4fc;font-weight:700;margin-bottom:1rem">Model Specification</div>
        <p><b style="color:#e2e8f0">Architecture:</b> YOLO11n (Nano)</p>
        <p><b style="color:#e2e8f0">Backbone:</b> YOLO11n custom-trained</p>
        <p><b style="color:#e2e8f0">Checkpoint:</b> best.pt</p>
        <p><b style="color:#e2e8f0">Input Size:</b> 800 × 800 px</p>
        <p><b style="color:#e2e8f0">Default Conf Threshold:</b> 0.45</p>
        <p><b style="color:#e2e8f0">Default IoU Threshold:</b> 0.45</p>
        <p><b style="color:#e2e8f0">Classes:</b> pothole</p>
        <p><b style="color:#e2e8f0">Annotation Format:</b> Pascal VOC XML → YOLO</p>
    </div>
    """, unsafe_allow_html=True)

# ── Section: Experiment Results ───────────────────────────────────────────────
if not exp_df.empty:
    st.markdown("---")
    section_header("Experiment Results", "All recorded experiment evaluations from research_reports/")
    st.dataframe(exp_df, use_container_width=True, hide_index=False)
    exp_csv = exp_df.to_csv(index=False).encode()
    st.download_button("⬇️ Download Experiment Results CSV", data=exp_csv,
                       file_name="experiment_results.csv", mime="text/csv")

# ── Section: Training Audit ────────────────────────────────────────────────
if not train_df.empty:
    st.markdown("---")
    section_header("Training Audit Log", "Phase-by-phase training history")
    st.dataframe(train_df, use_container_width=True, hide_index=False)

# ── Section: Operational Inference Stats ──────────────────────────────────────
st.markdown("---")
section_header("Operational Inference Statistics", "From actual detections in the application database")

try:
    dets = get_detections(limit=5000)
    if dets:
        df_ops = pd.DataFrame(dets)
        n_total = len(df_ops)
        avg_conf = df_ops["confidence"].mean() if "confidence" in df_ops.columns else 0
        if "severity" in df_ops.columns:
            sev_dist = df_ops["severity"].value_counts().reset_index()
            sev_dist.columns = ["Severity", "Count"]

        op_cards = [
            kpi_card(n_total,              "Total Saved Detections", "🔍", accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
            kpi_card(f"{avg_conf:.3f}",    "Avg. Confidence",        "📊", accent="linear-gradient(90deg,#8b5cf6,#ec4899)"),
        ]
        kpi_grid(op_cards)

        op_c1, op_c2 = st.columns(2)
        with op_c1:
            # Confidence histogram
            fig_hist = px.histogram(
                df_ops, x="confidence", nbins=20,
                title="Operational Confidence Distribution",
                color_discrete_sequence=["#6366f1"],
                template="plotly_dark",
                labels={"confidence": "Confidence Score", "count": "Detections"},
            )
            fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                    font_color="#c4c4e0")
            st.plotly_chart(fig_hist, use_container_width=True)

        with op_c2:
            if "severity" in df_ops.columns:
                SCOL = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
                fig_sev = px.pie(sev_dist, values="Count", names="Severity",
                                  color="Severity", color_discrete_map=SCOL,
                                  hole=0.55, template="plotly_dark",
                                  title="Operational Severity Distribution")
                fig_sev.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                                       margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_sev, use_container_width=True)

        # Source types
        if "source_type" in df_ops.columns:
            st_dist = df_ops["source_type"].value_counts().reset_index()
            st_dist.columns = ["Source Type", "Count"]
            fig_src = px.bar(st_dist, x="Source Type", y="Count",
                              color="Source Type", template="plotly_dark",
                              color_discrete_sequence=["#6366f1", "#ec4899", "#10b981"],
                              title="Detections by Source Type")
            fig_src.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#c4c4e0", showlegend=False)
            st.plotly_chart(fig_src, use_container_width=True)
    else:
        empty_state("No Detection Records Yet",
                    "Run Live Detection to populate operational inference stats.", "🔍")
except Exception as e:
    st.error(f"Could not load operational stats: {e}")

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.markdown("---")
info_box(
    "⚠️ <b>Important:</b> Validation and test metrics reflect performance on a specific "
    "665-image dataset with particular road/lighting conditions. Real-world performance "
    "may vary with different environments, camera angles, or road surface types. "
    "Operational inference results (above) come from saved detections and are subject "
    "to the image quality and operator decisions made during actual usage.",
    kind="warn",
)
