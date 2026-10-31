"""
8_Simulation_Lab.py — Isolated Scenario Simulation Lab for RoadSight.

ALL data on this page is SIMULATED.
Simulated records are isolated in simulation_runs / simulation_records tables
and NEVER appear in real dashboards, detection history, or analytics.
"""

from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from src.database import (
    save_simulation_run, get_simulation_runs,
    get_simulation_records, delete_simulation_run, init_db,
)
from src.ui_components import (
    inject_css, hero_banner, section_header, info_box,
    empty_state, kpi_card, kpi_grid, simulated_banner,
)

st.set_page_config(page_title="Simulation Lab · RoadSight", page_icon="🔬", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

hero_banner(
    "Simulation & Scenario Lab",
    "Configure and compare hypothetical road-maintenance scenarios — all data is clearly simulated",
    "🔬",
    badge="⚠ SIMULATED DATA — Never contaminates real records",
)

simulated_banner()
info_box(
    "Every record, chart and map on this page is <b>simulated</b>. "
    "Simulated data lives in isolated database tables and is never mixed with "
    "real detection history, repair records, or model evaluation results.",
    kind="sim",
)

# ─────────────────────────────────────────────────────────────────────────────
# Simulation engine helpers
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
SEVERITY_COSTS  = {"Low": 500, "Medium": 1500, "High": 4000, "Critical": 10000}
AREA_TEMPLATES  = [
    "North Zone", "South Zone", "East Zone", "West Zone", "Central District",
    "Industrial Area", "Residential Block A", "Residential Block B",
    "Highway Segment 1", "Highway Segment 2", "Market Road", "School Zone",
]

# India bounding box for simulated GPS
LAT_RANGE = (8.4, 37.6)
LON_RANGE = (68.7, 97.4)


def simulate_potholes(
    n: int,
    severity_weights: dict,
    area_names: list[str],
    repair_capacity: int,
    repair_duration_days: int,
    budget: float,
    strategy: str,
    seed: int = 42,
) -> tuple[list[dict], dict]:
    """Generate n simulated pothole records with configurable parameters."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    severities = list(severity_weights.keys())
    weights    = [severity_weights[s] / 100 for s in severities]

    records = []
    total_cost = 0.0
    for i in range(n):
        sev       = rng.choices(severities, weights=weights, k=1)[0]
        area      = rng.choice(area_names)
        est_cost  = SEVERITY_COSTS[sev] * rng.uniform(0.8, 1.3)
        days_rep  = max(1, int(np_rng.normal(repair_duration_days, repair_duration_days * 0.3)))

        lat = rng.uniform(*LAT_RANGE)
        lon = rng.uniform(*LON_RANGE)

        total_cost += est_cost
        records.append({
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "severity": sev,
            "status": "Simulated — Detected",
            "est_cost": round(est_cost, 2),
            "days_to_repair": days_rep,
            "area_name": area,
        })

    # Apply repair strategy ordering
    if strategy == "Priority (Highest Severity First)":
        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        records.sort(key=lambda r: order.get(r["severity"], 9))
    elif strategy == "Priority (Lowest Cost First)":
        records.sort(key=lambda r: r["est_cost"])
    elif strategy == "Geographic Clustering":
        records.sort(key=lambda r: r["area_name"])
    # else: FIFO — keep original order

    # Simulate repair progress given capacity and budget
    repaired_count = 0
    remaining_budget = budget
    for j, r in enumerate(records):
        if j < repair_capacity * repair_duration_days and r["est_cost"] <= remaining_budget:
            r["status"] = "Simulated — Repaired"
            remaining_budget -= r["est_cost"]
            repaired_count += 1

    sev_counts = {s: sum(1 for r in records if r["severity"] == s) for s in SEVERITY_LEVELS}
    status_counts = {}
    for r in records:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    summary = {
        "total_potholes": n,
        "total_est_cost": round(total_cost, 2),
        "repaired_count": repaired_count,
        "repair_rate_pct": round(repaired_count / max(n, 1) * 100, 1),
        "budget_used": round(budget - remaining_budget, 2),
        "remaining_budget": round(remaining_budget, 2),
        "severity_counts": sev_counts,
        "status_counts": status_counts,
        "strategy": strategy,
    }
    return records, summary


def detection_trend_df(n_potholes: int, n_days: int = 30, seed: int = 42) -> pd.DataFrame:
    """Simulate daily detection counts over n_days."""
    rng = np.random.default_rng(seed)
    base = n_potholes / n_days
    counts = rng.poisson(base, size=n_days).tolist()
    dates  = [(datetime.now(tz=timezone.utc) - timedelta(days=n_days - i)).strftime("%Y-%m-%d")
              for i in range(n_days)]
    return pd.DataFrame({"date": dates, "detections": counts})


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_config, tab_results, tab_history, tab_compare = st.tabs([
    "⚙️ Configure Scenario",
    "📊 Scenario Results",
    "📋 Saved Scenarios",
    "🔄 Compare Scenarios",
])

# ████████████████████████████████████████████████████████████████████████████
# TAB 1 — CONFIGURE
# ████████████████████████████████████████████████████████████████████████████
with tab_config:
    section_header("Scenario Configuration", "Set parameters for your simulated road-maintenance scenario")

    c1, c2 = st.columns(2)
    with c1:
        sim_name = st.text_input("Scenario Name", value="Scenario A", key="sim_name",
                                  placeholder="e.g. High-Budget Priority Strategy")
        sim_desc = st.text_area("Description (optional)", height=68, key="sim_desc")
        n_potholes = st.slider("Number of simulated potholes", 10, 2000, 200, step=10, key="sim_n")
        n_days_trend = st.slider("Detection period (days)", 7, 90, 30, key="sim_days")

    with c2:
        strategy = st.selectbox(
            "Repair prioritisation strategy",
            ["Priority (Highest Severity First)", "Priority (Lowest Cost First)",
             "Geographic Clustering", "FIFO (First Detected)"],
            key="sim_strategy",
        )
        repair_capacity = st.slider("Repair team capacity (jobs/day)", 1, 50, 5, key="sim_cap")
        repair_duration = st.slider("Average repair duration (days)", 1, 30, 5, key="sim_dur")
        budget = st.number_input("Total repair budget (₹)", min_value=0, max_value=50_000_000,
                                  value=1_000_000, step=50_000, key="sim_budget")

    section_header("Severity Distribution", "Adjust the percentage of each severity level (should sum ≈ 100)")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1: w_low      = st.slider("Low (%)",      0, 100, 30, key="w_low")
    with sc2: w_medium   = st.slider("Medium (%)",   0, 100, 40, key="w_med")
    with sc3: w_high     = st.slider("High (%)",     0, 100, 20, key="w_high")
    with sc4: w_critical = st.slider("Critical (%)", 0, 100, 10, key="w_crit")

    total_w = w_low + w_medium + w_high + w_critical
    if total_w == 0:
        st.warning("Severity weights sum to 0. Defaulting to equal distribution.")
        sev_weights = {"Low": 25, "Medium": 25, "High": 25, "Critical": 25}
    else:
        sev_weights = {"Low": w_low, "Medium": w_medium, "High": w_high, "Critical": w_critical}

    section_header("Geographic Areas")
    area_input = st.multiselect(
        "Areas to include in simulation",
        AREA_TEMPLATES,
        default=AREA_TEMPLATES[:6],
        key="sim_areas",
    )
    custom_area = st.text_input("Add custom area (optional)", key="sim_custom_area")
    if custom_area.strip():
        area_input = area_input + [custom_area.strip()]

    if not area_input:
        area_input = ["General Area"]

    sim_seed = st.number_input("Random seed (for reproducibility)", min_value=0, max_value=9999,
                                value=42, key="sim_seed")

    col_run, col_save = st.columns(2)
    run_btn  = col_run.button("▶️ Run Simulation", key="run_sim", use_container_width=True)
    save_btn = col_save.button("💾 Run & Save Scenario", key="save_sim", use_container_width=True)

    if run_btn or save_btn:
        with st.spinner("Running simulation…"):
            records, summary = simulate_potholes(
                n=n_potholes,
                severity_weights=sev_weights,
                area_names=area_input,
                repair_capacity=repair_capacity,
                repair_duration_days=repair_duration,
                budget=float(budget),
                strategy=strategy,
                seed=int(sim_seed),
            )
        st.session_state["sim_records"] = records
        st.session_state["sim_summary"] = summary
        st.session_state["sim_trend_df"] = detection_trend_df(n_potholes, n_days_trend, int(sim_seed))
        st.session_state["sim_config"]   = {
            "name": sim_name, "n_potholes": n_potholes, "strategy": strategy,
            "repair_capacity": repair_capacity, "repair_duration": repair_duration,
            "budget": budget, "severity_weights": sev_weights, "areas": area_input,
            "n_days_trend": n_days_trend, "seed": int(sim_seed),
        }

        if save_btn:
            try:
                run_id = save_simulation_run(
                    name=sim_name or "Unnamed Scenario",
                    description=sim_desc or "",
                    config_dict=st.session_state["sim_config"],
                    result_summary=summary,
                    records=records,
                )
                st.success(f"✅ Scenario saved! ID: `{run_id[:8]}…`")
            except Exception as e:
                st.error(f"Failed to save scenario: {e}")

        st.success(f"✅ Simulation complete — {n_potholes} potholes generated. Switch to **Scenario Results** tab.")


# ████████████████████████████████████████████████████████████████████████████
# TAB 2 — RESULTS
# ████████████████████████████████████████████████████████████████████████████
with tab_results:
    simulated_banner()

    if "sim_summary" not in st.session_state:
        empty_state("Run a Simulation First", "Go to 'Configure Scenario' to set parameters and run.", "🔬")
    else:
        summary = st.session_state["sim_summary"]
        records = st.session_state["sim_records"]
        trend_df = st.session_state.get("sim_trend_df", pd.DataFrame())
        cfg     = st.session_state.get("sim_config", {})

        # KPIs
        sev_counts = summary.get("severity_counts", {})
        cards = [
            kpi_card(summary["total_potholes"],     "Total Potholes",     "🔬", accent="linear-gradient(90deg,#a855f7,#8b5cf6)"),
            kpi_card(sev_counts.get("Critical", 0), "Critical",           "🔴", accent="linear-gradient(90deg,#ef4444,#f97316)"),
            kpi_card(sev_counts.get("High", 0),     "High",               "🟠", accent="linear-gradient(90deg,#f97316,#eab308)"),
            kpi_card(summary["repaired_count"],     "Repaired",           "✅", accent="linear-gradient(90deg,#10b981,#22c55e)"),
            kpi_card(f"{summary['repair_rate_pct']}%", "Repair Rate",     "📈", accent="linear-gradient(90deg,#22c55e,#84cc16)"),
            kpi_card(f"₹{summary['total_est_cost']:,.0f}", "Total Est. Cost", "💰", accent="linear-gradient(90deg,#ec4899,#a855f7)"),
            kpi_card(f"₹{summary['budget_used']:,.0f}",    "Budget Used",      "📉", accent="linear-gradient(90deg,#3b82f6,#6366f1)"),
            kpi_card(f"₹{summary['remaining_budget']:,.0f}", "Remaining Budget", "🏦", accent="linear-gradient(90deg,#6366f1,#8b5cf6)"),
        ]
        kpi_grid(cards)

        st.markdown(f"**Strategy:** `{summary['strategy']}`")
        st.markdown("---")

        # Charts
        ch1, ch2 = st.columns(2)

        with ch1:
            section_header("Severity Distribution [SIMULATED]")
            df_sev = pd.DataFrame(list(sev_counts.items()), columns=["Severity", "Count"])
            SCOL   = {"Low": "#22c55e", "Medium": "#eab308", "High": "#f97316", "Critical": "#ef4444"}
            fig_sev = px.pie(df_sev, values="Count", names="Severity",
                             color="Severity", color_discrete_map=SCOL,
                             hole=0.5, template="plotly_dark",
                             title="[SIMULATED] Severity Split")
            fig_sev.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0",
                                   margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_sev, use_container_width=True)

        with ch2:
            section_header("Repair Status [SIMULATED]")
            status_counts = summary.get("status_counts", {})
            if status_counts:
                df_stat = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
                fig_stat = px.bar(df_stat, x="Count", y="Status", orientation="h",
                                  color="Count", color_continuous_scale=["#a855f7", "#10b981"],
                                  template="plotly_dark",
                                  title="[SIMULATED] Repair Outcomes")
                fig_stat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                        font_color="#c4c4e0", coloraxis_showscale=False,
                                        margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_stat, use_container_width=True)

        # Detection trend
        section_header("Simulated Detection Trend [SIMULATED]")
        if not trend_df.empty:
            fig_trend = px.area(trend_df, x="date", y="detections",
                                title="[SIMULATED] Daily Detection Count",
                                color_discrete_sequence=["#a855f7"],
                                template="plotly_dark")
            fig_trend.update_traces(fillcolor="rgba(168,85,247,0.15)", line_color="#a855f7")
            fig_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                     font_color="#c4c4e0", xaxis_tickangle=-30,
                                     margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_trend, use_container_width=True)

        # Area breakdown
        section_header("Area-wise Simulated Pothole Count [SIMULATED]")
        df_rec = pd.DataFrame(records)
        if not df_rec.empty and "area_name" in df_rec.columns:
            area_grp = df_rec.groupby("area_name").agg(
                Count=("severity", "count"),
                Avg_Cost=("est_cost", "mean"),
            ).reset_index().sort_values("Count", ascending=False)

            fig_area = px.bar(area_grp, x="Count", y="area_name", orientation="h",
                              color="Count", color_continuous_scale=["#8b5cf6", "#ec4899"],
                              template="plotly_dark", title="[SIMULATED] Potholes by Area")
            fig_area.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                    font_color="#c4c4e0", coloraxis_showscale=False)
            st.plotly_chart(fig_area, use_container_width=True)

        # Workload projection
        section_header("Repair Workload Projection [SIMULATED]")
        cap = cfg.get("repair_capacity", 5)
        dur = cfg.get("repair_duration", 5)
        n   = cfg.get("n_potholes", 200)
        weeks_needed = max(1, int(np.ceil(n / max(cap * 7, 1))))
        team_days    = n * dur
        info_box(
            f"At <b>{cap} jobs/day</b> capacity: approx. <b>{weeks_needed} weeks</b> to clear all potholes. "
            f"Total team-days required: <b>{team_days:,}</b>.",
            kind="sim",
        )

        # Budget pie
        section_header("Budget Allocation [SIMULATED]")
        bc1, bc2 = st.columns(2)
        with bc1:
            budget_total = cfg.get("budget", 1_000_000)
            used = summary["budget_used"]
            remaining = summary["remaining_budget"]
            fig_bud = px.pie(
                values=[used, remaining],
                names=["Budget Used", "Remaining"],
                color_discrete_sequence=["#ec4899", "#10b981"],
                hole=0.6, template="plotly_dark",
                title="[SIMULATED] Budget Usage",
            )
            fig_bud.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#c4c4e0")
            st.plotly_chart(fig_bud, use_container_width=True)

        with bc2:
            st.markdown(f"""
            <div class="glass-card">
                <div style="color:#d8b4fe;font-weight:700;margin-bottom:1rem">Budget Summary [SIMULATED]</div>
                <p>Total Budget: <b style="color:#e2e8f0">₹{budget_total:,.0f}</b></p>
                <p>Budget Used: <b style="color:#ec4899">₹{used:,.0f}</b></p>
                <p>Remaining: <b style="color:#10b981">₹{remaining:,.0f}</b></p>
                <p>Repair Rate: <b style="color:#a5b4fc">{summary['repair_rate_pct']}%</b></p>
                <p>Est. Total Cost: <b style="color:#fbbf24">₹{summary['total_est_cost']:,.0f}</b></p>
            </div>""", unsafe_allow_html=True)

        # Export
        st.markdown("---")
        section_header("Export Simulated Data")
        sim_csv = df_rec.to_csv(index=False).encode()
        st.download_button("⬇️ Download Simulated Records CSV", data=sim_csv,
                           file_name="simulated_potholes.csv", mime="text/csv")
        sim_json = json.dumps({"summary": summary, "config": cfg}, indent=2, default=str).encode()
        st.download_button("⬇️ Download Scenario Summary JSON", data=sim_json,
                           file_name="scenario_summary.json", mime="application/json")


# ████████████████████████████████████████████████████████████████████████████
# TAB 3 — SAVED SCENARIOS
# ████████████████████████████████████████████████████████████████████████████
with tab_history:
    simulated_banner()
    section_header("Saved Simulation Scenarios")

    try:
        runs = get_simulation_runs()
    except Exception as e:
        st.error(f"Could not load scenarios: {e}")
        runs = []

    if not runs:
        empty_state("No Saved Scenarios", "Run a scenario and click 'Run & Save Scenario' to persist it.", "📋")
    else:
        for run in runs:
            cfg_data = {}
            summary_data = {}
            try:
                cfg_data     = json.loads(run.get("config_json") or "{}")
                summary_data = json.loads(run.get("result_summary") or "{}")
            except Exception:
                pass

            ts = (run.get("created_at") or "")[:16].replace("T", " ")
            n  = summary_data.get("total_potholes", "?")
            rr = summary_data.get("repair_rate_pct", "?")

            with st.expander(f"🔬 {run['name']} — {ts} | {n} potholes | {rr}% repaired"):
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.markdown(f"**Created:** {ts}")
                    st.markdown(f"**Strategy:** {cfg_data.get('strategy', '—')}")
                    st.markdown(f"**Potholes:** {n}")
                    st.markdown(f"**Budget:** ₹{cfg_data.get('budget', 0):,.0f}")
                    if run.get("description"):
                        st.caption(run["description"])
                with sc2:
                    if summary_data:
                        st.markdown(f"**Repaired:** {summary_data.get('repaired_count', '?')}")
                        st.markdown(f"**Repair Rate:** {rr}%")
                        st.markdown(f"**Est. Cost:** ₹{summary_data.get('total_est_cost', 0):,.0f}")
                        st.markdown(f"**Budget Used:** ₹{summary_data.get('budget_used', 0):,.0f}")

                col_load, col_del = st.columns(2)
                if col_load.button(f"📂 Load Records", key=f"load_{run['id']}"):
                    try:
                        recs    = get_simulation_records(run["id"])
                        rec_df  = pd.DataFrame(recs)
                        csv_out = rec_df.to_csv(index=False).encode()
                        col_load.download_button(
                            "⬇️ Download CSV",
                            data=csv_out,
                            file_name=f"sim_{run['id'][:8]}.csv",
                            mime="text/csv",
                            key=f"dl_{run['id']}",
                        )
                    except Exception as e:
                        st.error(f"Load error: {e}")

                if col_del.button(f"🗑️ Delete", key=f"del_{run['id']}"):
                    try:
                        delete_simulation_run(run["id"])
                        st.success("Scenario deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")


# ████████████████████████████████████████████████████████████████████████████
# TAB 4 — COMPARE
# ████████████████████████████████████████████████████████████████████████████
with tab_compare:
    simulated_banner()
    section_header("Compare Scenarios", "Compare two saved simulation scenarios side by side")

    try:
        runs = get_simulation_runs()
    except Exception:
        runs = []

    if len(runs) < 2:
        info_box("Save at least 2 scenarios to compare them here.", kind="info")
    else:
        run_names = [f"{r['name']} ({r['created_at'][:10]})" for r in runs]
        cc1, cc2  = st.columns(2)
        with cc1:
            sel_a = st.selectbox("Scenario A", run_names, index=0, key="cmp_a")
        with cc2:
            sel_b = st.selectbox("Scenario B", run_names, index=min(1, len(run_names)-1), key="cmp_b")

        run_a = runs[run_names.index(sel_a)]
        run_b = runs[run_names.index(sel_b)]

        def _parse_summary(run: dict) -> dict:
            try:
                return json.loads(run.get("result_summary") or "{}")
            except Exception:
                return {}

        sa, sb = _parse_summary(run_a), _parse_summary(run_b)

        metrics = [
            ("Total Potholes",    sa.get("total_potholes", 0),     sb.get("total_potholes", 0)),
            ("Repaired",          sa.get("repaired_count", 0),      sb.get("repaired_count", 0)),
            ("Repair Rate (%)",   sa.get("repair_rate_pct", 0),     sb.get("repair_rate_pct", 0)),
            ("Est. Total Cost ₹", sa.get("total_est_cost", 0),      sb.get("total_est_cost", 0)),
            ("Budget Used ₹",     sa.get("budget_used", 0),         sb.get("budget_used", 0)),
            ("Remaining Budget ₹",sa.get("remaining_budget", 0),    sb.get("remaining_budget", 0)),
        ]

        df_cmp = pd.DataFrame(metrics, columns=["Metric", sel_a, sel_b])
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Bar(name=sel_a, x=df_cmp["Metric"], y=df_cmp[sel_a],
                                  marker_color="#8b5cf6"))
        fig_cmp.add_trace(go.Bar(name=sel_b, x=df_cmp["Metric"], y=df_cmp[sel_b],
                                  marker_color="#ec4899"))
        fig_cmp.update_layout(
            barmode="group", template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c4c4e0",
            title="[SIMULATED] Scenario Comparison",
            xaxis_tickangle=-20,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        st.dataframe(df_cmp.set_index("Metric"), use_container_width=True)
