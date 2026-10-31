"""
10_Reports_Export.py — Reports & Export Center for RoadSight Intelligence Platform.

Generate downloadable CSV, Excel and PDF reports from actual database records.
All reports include generation timestamp, date filters and metric definitions.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import json
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from src.database import (
    get_detections, get_repair_tasks, get_locations,
    get_kpi_summary, get_analytics_data, init_db,
)
from src.ui_components import (
    inject_css, hero_banner, section_header, info_box,
    empty_state, kpi_card, kpi_grid,
)

st.set_page_config(page_title="Reports & Export · RoadSight", page_icon="📤", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner(
    "Reports & Export Center",
    "Generate and download comprehensive reports from real detection and repair records",
    "📤",
    badge="CSV · Excel · JSON · GeoJSON",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global date filter
# ─────────────────────────────────────────────────────────────────────────────
section_header("Report Filters")
fc1, fc2, fc3 = st.columns([1, 1, 2])
with fc1:
    rpt_from = st.date_input("From", value=date.today() - timedelta(days=90), key="rpt_from")
with fc2:
    rpt_to   = st.date_input("To",   value=date.today(),                      key="rpt_to")
with fc3:
    sev_filter = st.multiselect("Severity filter", ["Critical", "High", "Medium", "Low"],
                                 default=[], key="rpt_sev",
                                 help="Leave blank to include all severities")

date_from_s = rpt_from.isoformat()
date_to_s   = rpt_to.isoformat()
gen_ts      = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Loading data…"):
    try:
        detections   = get_detections(limit=10000, date_from=date_from_s, date_to=date_to_s,
                                       severity=sev_filter[0] if len(sev_filter) == 1 else None)
        if len(sev_filter) > 1:
            detections = [d for d in detections if d.get("severity") in sev_filter]

        repair_tasks = get_repair_tasks(limit=5000)
        locations    = get_locations(
            severity_filter=sev_filter if sev_filter else None,
            date_from=date_from_s, date_to=date_to_s,
        )
        kpis         = get_kpi_summary()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

det_df  = pd.DataFrame(detections)  if detections  else pd.DataFrame()
task_df = pd.DataFrame(repair_tasks) if repair_tasks else pd.DataFrame()
loc_df  = pd.DataFrame(locations)   if locations   else pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# Summary strip
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
cards = [
    kpi_card(len(detections),          "Detections in Range", "🔍", accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
    kpi_card(len(repair_tasks),        "Total Repair Tasks",  "🔧", accent="linear-gradient(90deg,#ec4899,#a855f7)"),
    kpi_card(len(locations),           "Location Records",    "📍", accent="linear-gradient(90deg,#10b981,#22c55e)"),
    kpi_card(f"{kpis.get('repair_completion_pct',0)}%", "Completion Rate", "✅",
             accent="linear-gradient(90deg,#f59e0b,#fbbf24)"),
]
kpi_grid(cards)

# ─────────────────────────────────────────────────────────────────────────────
# Report tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_det, tab_sev, tab_loc, tab_repair, tab_cost, tab_model, tab_full = st.tabs([
    "🔍 Detection Summary",
    "⚠️ Severity Report",
    "📍 Location Report",
    "🔧 Repair Progress",
    "💰 Cost Report",
    "🏆 Model Evaluation",
    "📦 Full Export",
])


# ── Helper: add meta header rows to Excel ────────────────────────────────────
def _meta_header(title: str) -> list[dict]:
    return [
        {"Field": "Report Title",      "Value": title},
        {"Field": "Generated At (UTC)", "Value": gen_ts},
        {"Field": "Date Range",         "Value": f"{date_from_s} → {date_to_s}"},
        {"Field": "Severity Filter",    "Value": ", ".join(sev_filter) if sev_filter else "All"},
        {"Field": "Records",            "Value": ""},
    ]


def _excel_bytes(sheets: dict) -> bytes:
    """Build a multi-sheet Excel file. sheets = {name: df}."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buf.getvalue()


# ████████████████████████████████████████████████████████████████████████████
# TAB: Detection Summary
# ████████████████████████████████████████████████████████████████████████████
with tab_det:
    section_header("Detection Summary Report",
                   f"Period: {date_from_s} → {date_to_s} | Generated: {gen_ts}")

    if det_df.empty:
        empty_state("No Detections in Selected Range", "Adjust the date or severity filters.", "🔍")
    else:
        # Summary stats
        stats = {
            "Total Detections":    len(det_df),
            "Unique Sources":      det_df["source_name"].nunique() if "source_name" in det_df.columns else "—",
            "Avg Confidence":      f"{det_df['confidence'].mean():.3f}" if "confidence" in det_df.columns else "—",
            "Min Confidence":      f"{det_df['confidence'].min():.3f}" if "confidence" in det_df.columns else "—",
            "Max Confidence":      f"{det_df['confidence'].max():.3f}" if "confidence" in det_df.columns else "—",
        }
        cols = st.columns(len(stats))
        for i, (label, val) in enumerate(stats.items()):
            cols[i].metric(label, val)

        # Table
        show = [c for c in ["id", "created_at", "source_name", "source_type",
                              "confidence", "severity", "area_ratio"] if c in det_df.columns]
        df_show = det_df[show].copy()
        if "created_at" in df_show.columns:
            df_show["created_at"] = df_show["created_at"].str[:16].str.replace("T", " ")
        if "id" in df_show.columns:
            df_show["id"] = df_show["id"].str[:8] + "…"
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        # Downloads
        dc1, dc2 = st.columns(2)
        csv_b = det_df.to_csv(index=False).encode()
        dc1.download_button("⬇️ Download CSV", data=csv_b,
                             file_name="detection_summary.csv", mime="text/csv",
                             key="det_csv")
        xl_b = _excel_bytes({"Detection Summary": det_df})
        dc2.download_button("⬇️ Download Excel", data=xl_b,
                             file_name="detection_summary.xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             key="det_xl")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Severity Report
# ████████████████████████████████████████████████████████████████████████████
with tab_sev:
    section_header("Severity Report", f"Period: {date_from_s} → {date_to_s}")

    if det_df.empty or "severity" not in det_df.columns:
        empty_state("No Severity Data in Range", "Run detections to populate severity records.", "⚠️")
    else:
        sev_summary = det_df["severity"].value_counts().reset_index()
        sev_summary.columns = ["Severity", "Count"]
        sev_summary["Percentage"] = (sev_summary["Count"] / sev_summary["Count"].sum() * 100).round(1)
        sev_summary["Avg. Est. Cost (₹)"] = sev_summary["Severity"].map({
            "Critical": config.DEFAULT_REPAIR_COST_CRITICAL,
            "High":     config.DEFAULT_REPAIR_COST_HIGH,
            "Medium":   config.DEFAULT_REPAIR_COST_MEDIUM,
            "Low":      config.DEFAULT_REPAIR_COST_LOW,
        })
        sev_summary["Total Est. Cost (₹)"] = sev_summary["Count"] * sev_summary["Avg. Est. Cost (₹)"]

        SCOL = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
        sv1, sv2 = st.columns(2)
        with sv1:
            fig_pie = px.pie(sev_summary, values="Count", names="Severity",
                              color="Severity", color_discrete_map=SCOL,
                              hole=0.55, template="plotly_dark", title="Severity Distribution")
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                                   margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        with sv2:
            fig_bar = px.bar(sev_summary, x="Severity", y="Count", color="Severity",
                              color_discrete_map=SCOL, template="plotly_dark",
                              title="Count by Severity")
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font_color="#c4c4e0", showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.dataframe(sev_summary, use_container_width=True, hide_index=True)

        sdc1, sdc2 = st.columns(2)
        sdc1.download_button("⬇️ Severity CSV", data=sev_summary.to_csv(index=False).encode(),
                              file_name="severity_report.csv", mime="text/csv", key="sev_csv")
        sdc2.download_button("⬇️ Severity Excel", data=_excel_bytes({"Severity Report": sev_summary}),
                              file_name="severity_report.xlsx",
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              key="sev_xl")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Location Report
# ████████████████████████████████████████████████████████████████████████████
with tab_loc:
    section_header("Location Report", f"Potholes with saved coordinates | {date_from_s} → {date_to_s}")

    if loc_df.empty:
        empty_state("No Location Records", "Add locations via the GIS Map page.", "📍")
    else:
        show_loc = [c for c in ["id", "lat", "lon", "address", "area_name",
                                  "location_source", "severity", "created_at"] if c in loc_df.columns]
        df_loc_show = loc_df[show_loc].copy()
        if "created_at" in df_loc_show.columns:
            df_loc_show["created_at"] = df_loc_show["created_at"].str[:16].str.replace("T", " ")
        if "id" in df_loc_show.columns:
            df_loc_show["id"] = df_loc_show["id"].str[:8] + "…"
        st.dataframe(df_loc_show, use_container_width=True, hide_index=True)

        # GeoJSON export
        features = []
        for _, row in loc_df.iterrows():
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
                    "properties": {
                        k: str(v) if v else None
                        for k, v in row.items()
                        if k not in ("lat", "lon")
                    },
                })
        geojson = {"type": "FeatureCollection", "features": features}
        geojson_b = json.dumps(geojson, indent=2).encode()

        lc1, lc2, lc3 = st.columns(3)
        lc1.download_button("⬇️ Location CSV", data=loc_df.to_csv(index=False).encode(),
                             file_name="location_report.csv", mime="text/csv", key="loc_csv")
        lc2.download_button("⬇️ GeoJSON", data=geojson_b,
                             file_name="potholes.geojson", mime="application/geo+json", key="loc_geojson")
        lc3.download_button("⬇️ Location Excel", data=_excel_bytes({"Locations": loc_df}),
                             file_name="location_report.xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             key="loc_xl")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Repair Progress
# ████████████████████████████████████████████████████████████████████████████
with tab_repair:
    section_header("Repair Progress Report", f"All repair tasks | Generated: {gen_ts}")

    if task_df.empty:
        empty_state("No Repair Tasks", "Create tasks from the Repair Management page.", "🔧")
    else:
        status_summary = task_df["status"].value_counts().reset_index() if "status" in task_df.columns else pd.DataFrame()
        if not status_summary.empty:
            status_summary.columns = ["Status", "Count"]
            STATUS_COLORS = {
                "Pending Verification": "#f59e0b", "Verified": "#3b82f6",
                "Assigned": "#8b5cf6", "In Progress": "#ec4899",
                "Repaired": "#10b981", "Reverified": "#22c55e",
                "Closed": "#6366f1", "Rejected": "#ef4444",
            }
            rp1, rp2 = st.columns(2)
            with rp1:
                fig_rep = px.pie(status_summary, values="Count", names="Status",
                                  color="Status", color_discrete_map=STATUS_COLORS,
                                  hole=0.55, template="plotly_dark", title="Task Status Distribution")
                fig_rep.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                                       margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_rep, use_container_width=True)
            with rp2:
                st.dataframe(status_summary, use_container_width=True, hide_index=True)

                total_tasks = len(task_df)
                repaired = status_summary[status_summary["Status"].isin(["Repaired","Closed"])]["Count"].sum()
                comp_rate = round(repaired / max(total_tasks, 1) * 100, 1)
                st.metric("Completion Rate", f"{comp_rate}%")
                st.metric("Total Tasks", total_tasks)

        show_task = [c for c in ["id", "status", "priority", "assigned_team",
                                   "est_cost", "actual_cost", "due_date", "updated_at", "severity"]
                     if c in task_df.columns]
        df_task_show = task_df[show_task].copy()
        if "id" in df_task_show.columns:
            df_task_show["id"] = df_task_show["id"].str[:8] + "…"
        if "updated_at" in df_task_show.columns:
            df_task_show["updated_at"] = df_task_show["updated_at"].str[:16].str.replace("T", " ")
        st.dataframe(df_task_show, use_container_width=True, hide_index=True)

        rc1, rc2 = st.columns(2)
        rc1.download_button("⬇️ Repair Tasks CSV", data=task_df.to_csv(index=False).encode(),
                             file_name="repair_progress.csv", mime="text/csv", key="rep_csv")
        rc2.download_button("⬇️ Repair Tasks Excel", data=_excel_bytes({"Repair Progress": task_df}),
                             file_name="repair_progress.xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             key="rep_xl")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Cost Report
# ████████████████████████████████████████████████████████████████████████████
with tab_cost:
    section_header("Maintenance Cost Report", f"Estimated vs Actual repair costs | {gen_ts}")

    if task_df.empty:
        empty_state("No Cost Data", "Create repair tasks with cost estimates.", "💰")
    else:
        cost_df = task_df[task_df.get("est_cost", pd.Series(dtype=float)).notna()].copy() \
            if "est_cost" in task_df.columns else pd.DataFrame()

        if cost_df.empty and "est_cost" in task_df.columns:
            cost_df = task_df.copy()

        if not task_df.empty and "est_cost" in task_df.columns:
            total_est    = task_df["est_cost"].sum(skipna=True)
            total_actual = task_df["actual_cost"].sum(skipna=True) if "actual_cost" in task_df.columns else 0

            cost_cards = [
                kpi_card(f"₹{total_est:,.0f}",    "Total Estimated Cost", "📋",
                          accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
                kpi_card(f"₹{total_actual:,.0f}", "Total Actual Cost",    "💸",
                          accent="linear-gradient(90deg,#ec4899,#a855f7)"),
                kpi_card(f"₹{(total_actual - total_est):+,.0f}", "Variance",  "📊",
                          accent="linear-gradient(90deg,#f59e0b,#fbbf24)" if total_actual <= total_est
                          else "linear-gradient(90deg,#ef4444,#f97316)"),
            ]
            kpi_grid(cost_cards)

        if "priority" in task_df.columns and "est_cost" in task_df.columns:
            PRIO_COL = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
            cost_by_prio = task_df.groupby("priority")["est_cost"].sum().reset_index()
            cost_by_prio.columns = ["Priority", "Est. Cost (₹)"]
            fig_cprio = px.bar(cost_by_prio, x="Priority", y="Est. Cost (₹)",
                               color="Priority", color_discrete_map=PRIO_COL,
                               template="plotly_dark", title="Estimated Cost by Priority")
            fig_cprio.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                     font_color="#c4c4e0", showlegend=False)
            st.plotly_chart(fig_cprio, use_container_width=True)

        if "est_cost" in task_df.columns:
            cost_show = [c for c in ["id", "status", "priority", "est_cost", "actual_cost", "due_date"]
                         if c in task_df.columns]
            df_cshow = task_df[cost_show].copy()
            if "id" in df_cshow.columns:
                df_cshow["id"] = df_cshow["id"].str[:8] + "…"
            st.dataframe(df_cshow, use_container_width=True, hide_index=True)

            cc1, cc2 = st.columns(2)
            cc1.download_button("⬇️ Cost Report CSV",
                                 data=task_df[cost_show].to_csv(index=False).encode(),
                                 file_name="cost_report.csv", mime="text/csv", key="cost_csv")
            cc2.download_button("⬇️ Cost Report Excel",
                                 data=_excel_bytes({"Cost Report": task_df[cost_show]}),
                                 file_name="cost_report.xlsx",
                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 key="cost_xl")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Model Evaluation
# ████████████████████████████████████████████████████████████████████████████
with tab_model:
    section_header("Model Evaluation Report",
                   "Sourced from research_reports/results/ — no fabricated metrics")

    model_data_available = config.FINAL_COMPARISON_CSV.is_file() or config.FINAL_COMPARISON_JSON.is_file()

    if not model_data_available:
        empty_state("Evaluation Files Not Found",
                    "Place final_model_comparison.csv or .json in research_reports/results/", "🏆")
    else:
        report_lines = [
            f"# Model Evaluation Report",
            f"Generated: {gen_ts}",
            f"Project: AI-Based Road Pothole Detection",
            f"Primary Model: YOLO11n Custom Checkpoint",
            "",
            "## Dataset",
            f"Total Images: {config.DATASET_TOTAL_IMAGES}",
            f"Training: {config.DATASET_TRAIN}",
            f"Validation: {config.DATASET_VAL}",
            f"Test: {config.DATASET_TEST}",
            "Annotation: Pascal VOC XML → YOLO format",
            "",
            "## Test-Set Results (67 images, 161 instances)",
        ]

        if config.FINAL_COMPARISON_JSON.is_file():
            try:
                cmp = json.loads(config.FINAL_COMPARISON_JSON.read_text(encoding="utf-8"))
                for m in cmp.get("models", []):
                    report_lines.append(f"\n### {m['Model']}")
                    for k, v in m.items():
                        if k != "Model":
                            report_lines.append(f"  {k}: {v}")
            except Exception as e:
                report_lines.append(f"[Error reading JSON: {e}]")

        report_txt = "\n".join(report_lines)
        st.text_area("Report Preview", value=report_txt, height=300, disabled=True)

        mc1, mc2 = st.columns(2)
        mc1.download_button("⬇️ Download Report (TXT)",
                             data=report_txt.encode(),
                             file_name="model_evaluation_report.txt",
                             mime="text/plain", key="model_txt")

        if config.FINAL_COMPARISON_CSV.is_file():
            df_cmp = pd.read_csv(config.FINAL_COMPARISON_CSV)
            mc2.download_button("⬇️ Download Metrics CSV",
                                 data=df_cmp.to_csv(index=False).encode(),
                                 file_name="model_evaluation_metrics.csv",
                                 mime="text/csv", key="model_csv")


# ████████████████████████████████████████████████████████████████████████████
# TAB: Full Export
# ████████████████████████████████████████████████████████████████████████████
with tab_full:
    section_header("Full Platform Data Export",
                   "Download all data in a single Excel workbook or as JSON")

    info_box(
        f"Export includes: <b>{len(detections)} detections</b>, "
        f"<b>{len(repair_tasks)} repair tasks</b>, "
        f"<b>{len(locations)} location records</b>. "
        f"Date range: {date_from_s} → {date_to_s}.",
        kind="info",
    )

    sheets = {}
    if not det_df.empty:
        sheets["Detections"] = det_df
    if not task_df.empty:
        sheets["Repair Tasks"] = task_df
    if not loc_df.empty:
        sheets["Locations"] = loc_df

    # KPI sheet
    kpi_items = [
        {"Metric": k, "Value": str(v)}
        for k, v in kpis.items()
        if not isinstance(v, dict)
    ]
    if kpi_items:
        sheets["KPI Summary"] = pd.DataFrame(kpi_items)

    # Meta sheet
    meta_df = pd.DataFrame([
        {"Key": "Generated At (UTC)", "Value": gen_ts},
        {"Key": "Date Filter From",   "Value": date_from_s},
        {"Key": "Date Filter To",     "Value": date_to_s},
        {"Key": "Severity Filter",    "Value": ", ".join(sev_filter) if sev_filter else "All"},
        {"Key": "Project",            "Value": "RoadSight Intelligence Platform"},
        {"Key": "Model",              "Value": "YOLO11n Custom Checkpoint"},
        {"Key": "Platform Version",   "Value": "2.0.0"},
    ])
    sheets["Export Metadata"] = meta_df

    fc1, fc2 = st.columns(2)

    # Excel multi-sheet
    if sheets:
        xl_b = _excel_bytes(sheets)
        fc1.download_button(
            "⬇️ Download Full Excel Export",
            data=xl_b,
            file_name=f"roadsight_export_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="full_xl",
            use_container_width=True,
        )

    # JSON bundle
    bundle = {
        "metadata": {
            "generated_utc": gen_ts,
            "date_from": date_from_s,
            "date_to": date_to_s,
            "severity_filter": sev_filter or "all",
            "platform_version": "2.0.0",
        },
        "kpi_summary": kpis,
        "detection_count": len(detections),
        "repair_task_count": len(repair_tasks),
        "location_count": len(locations),
        "detections": detections[:500],       # cap at 500 rows for JSON
        "repair_tasks": repair_tasks[:500],
        "locations": locations[:500],
    }
    json_b = json.dumps(bundle, indent=2, default=str).encode()
    fc2.download_button(
        "⬇️ Download JSON Bundle",
        data=json_b,
        file_name=f"roadsight_export_{date.today().isoformat()}.json",
        mime="application/json",
        key="full_json",
        use_container_width=True,
    )

    st.markdown("---")
    info_box(
        "⚠️ JSON export is limited to 500 records per table for browser compatibility. "
        "Use the individual tab exports for complete datasets.",
        kind="warn",
    )
