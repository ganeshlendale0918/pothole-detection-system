"""
6_Repair_Management.py — Full repair lifecycle management for RoadSight.
Lifecycle: Pending Verification → Verified → Assigned → In Progress → Repaired → Reverified → Closed
Fixes: st.metric() KPIs, before/after image upload, full task detail panel,
       image persistence, real-time updates via periodic rerun.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

import config
from src.database import (
    VALID_STATUSES, create_repair_task, get_detections, get_repair_kpis,
    get_repair_status_log, get_repair_task_by_id, get_repair_tasks,
    init_db, transition_repair_status, update_repair_task,
)
from src.ui_components import (
    empty_state, hero_banner, info_box, inject_css,
    section_header, severity_pill, status_pill,
)

st.set_page_config(page_title="Repair Management · RoadSight", page_icon="🔧", layout="wide")
init_db()
inject_css()

with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### ⚙️ Dashboard Controls")
    auto_refresh = st.checkbox("Auto-refresh (10s)", value=False, key="rm_autorefresh")
    if st.button("🔄 Refresh Now", key="rm_refresh_btn"):
        st.rerun()

hero_banner(
    "Repair & Maintenance Management",
    "Manage the full repair lifecycle from detection to closure",
    "🔧",
    badge="Detected → Verified → Assigned → In Progress → Repaired → Closed",
)

# ── KPIs via st.metric() ──────────────────────────────────────────────────────
try:
    kpis = get_repair_kpis()
except Exception as e:
    kpis = {}
    st.error(f"KPI error: {e}")

dist = kpis.get("status_distribution", {})

section_header("Repair KPIs")
k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
k1.metric("📋 Total Tasks",      kpis.get("total_tasks", 0))
k2.metric("🕐 Pending Verify",   dist.get("Pending Verification", 0))
k3.metric("✅ Verified",          dist.get("Verified", 0))
k4.metric("🔧 In Progress",       dist.get("In Progress", 0))
k5.metric("🏁 Repaired/Closed",   kpis.get("repaired", 0))
k6.metric("📈 Completion",         f"{kpis.get('completion_pct', 0):.1f}%")
k7.metric("⚠️ Overdue",           kpis.get("overdue", 0))

c1, c2 = st.columns(2)
with c1:
    st.metric("💰 Est. Total Cost",    f"₹{kpis.get('est_total_cost', 0):,.0f}")
with c2:
    st.metric("💵 Actual Total Cost",  f"₹{kpis.get('actual_total_cost', 0):,.0f}")

if kpis.get("overdue", 0) > 0:
    info_box(
        f"⚠️ <b>{kpis['overdue']} repair task(s) are overdue.</b> "
        "Update their status or extend due dates.",
        kind="warn",
    )

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_list, tab_create, tab_detail = st.tabs(["📋 Task List", "➕ Create Task", "🔍 Task Detail & Update"])

# ─────────────────────────────────────────────────────────────────────────────
# TASK LIST
# ─────────────────────────────────────────────────────────────────────────────
with tab_list:
    section_header("All Repair Tasks")
    tf1, tf2, tf3 = st.columns(3)
    with tf1:
        status_f = st.selectbox("Filter by status", ["All"] + VALID_STATUSES, key="rm_sf")
    with tf2:
        prio_f = st.selectbox("Filter by priority", ["All", "Critical", "High", "Medium", "Low"], key="rm_pf")
    with tf3:
        show_overdue = st.checkbox("Overdue only", key="rm_overdue_only")

    tasks = get_repair_tasks(
        status=None if status_f == "All" else status_f,
        priority=None if prio_f == "All" else prio_f,
        limit=200,
    )

    if show_overdue:
        today_str = date.today().isoformat()
        tasks = [
            t for t in tasks
            if t.get("due_date") and t["due_date"] < today_str
            and t.get("status") not in ("Repaired", "Closed", "Rejected")
        ]

    if not tasks:
        empty_state("No Repair Tasks", "Create tasks from the 'Create Task' tab.", "🔧")
    else:
        df_t = pd.DataFrame(tasks)
        show_cols = ["id", "status", "priority", "assigned_team", "assigned_worker",
                     "est_cost", "actual_cost", "due_date", "updated_at", "severity"]
        avail = [c for c in show_cols if c in df_t.columns]
        df_show = df_t[avail].copy()
        df_show["id"] = df_show["id"].str[:10] + "…"
        if "updated_at" in df_show.columns:
            df_show["updated_at"] = df_show["updated_at"].str[:16].str.replace("T", " ")
        if "due_date" in df_show.columns:
            today_iso = date.today().isoformat()
            # Highlight overdue
            df_show["⚠"] = df_show.apply(
                lambda r: "🔴 OVERDUE" if (
                    r.get("due_date") and r["due_date"] < today_iso
                    and str(r.get("status", "")) not in ("Repaired", "Closed", "Rejected")
                ) else "", axis=1
            )
        df_show.columns = [c.replace("_", " ").title() if c != "⚠" else "⚠" for c in df_show.columns]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        dl_csv = df_t[avail].to_csv(index=False).encode()
        st.download_button("⬇️ Download Task List CSV", data=dl_csv,
                           file_name="repair_tasks.csv", mime="text/csv")
        st.caption("📋 Copy a full Task ID from the database row, then paste it in 'Task Detail & Update' to manage it.")


# ─────────────────────────────────────────────────────────────────────────────
# CREATE TASK
# ─────────────────────────────────────────────────────────────────────────────
with tab_create:
    section_header("Create New Repair Task")

    info_box(
        "Link this task to an existing detection. The detection's severity, confidence, "
        "and source will be automatically associated.",
        kind="info",
    )

    # Detection selector
    recent_dets = get_detections(limit=50)
    det_opts = ["None — standalone task"] + [
        f"{d['id'][:8]}… | {d.get('source_name','?')[:40]} | {d.get('severity','?')} | conf:{d.get('confidence',0):.2f}"
        for d in recent_dets
    ]
    det_sel = st.selectbox("Link to detection (optional)", det_opts, key="rm_det_sel")

    # Show detection preview
    if det_sel != "None — standalone task":
        idx = det_opts.index(det_sel) - 1
        if 0 <= idx < len(recent_dets):
            chosen_det = recent_dets[idx]
            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("Severity", chosen_det.get("severity") or "—")
            pc2.metric("Confidence", f"{chosen_det.get('confidence',0):.3f}")
            pc3.metric("Source", chosen_det.get("source_type", "—"))
            pc4.metric("Recorded", (chosen_det.get("created_at","")[:10]))

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        prio = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=2, key="rm_prio")
        team = st.text_input("Assigned team", key="rm_team", placeholder="e.g. Ward 5 Repair Crew")
        worker = st.text_input("Assigned worker", key="rm_worker", placeholder="e.g. Rajan Kumar")
    with c2:
        due = st.date_input("Due date", value=date.today() + timedelta(days=7), key="rm_due")
        cost_d = {
            "Critical": config.DEFAULT_REPAIR_COST_CRITICAL,
            "High": config.DEFAULT_REPAIR_COST_HIGH,
            "Medium": config.DEFAULT_REPAIR_COST_MEDIUM,
            "Low": config.DEFAULT_REPAIR_COST_LOW,
        }
        est_cost = st.number_input(
            "Estimated cost (₹)", min_value=0,
            value=int(cost_d.get(prio, 1500)), key="rm_cost",
        )

    notes = st.text_area("Repair notes", key="rm_notes", height=80,
                          placeholder="Describe the scope of work, materials needed, etc.")

    if st.button("✅ Create Repair Task", key="rm_create", type="primary"):
        det_id = None
        if det_sel != "None — standalone task":
            idx = det_opts.index(det_sel) - 1
            det_id = recent_dets[idx]["id"] if 0 <= idx < len(recent_dets) else None
        try:
            tid = create_repair_task(
                detection_id=det_id,
                priority=prio,
                assigned_team=team.strip() or None,
                assigned_worker=worker.strip() or None,
                due_date=due.isoformat(),
                est_cost=float(est_cost) or None,
                repair_notes=notes.strip() or None,
            )
            st.success(f"✅ Repair task created! Task ID: `{tid}`")
            st.info("Copy the Task ID above, then open 'Task Detail & Update' to manage it.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to create task: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TASK DETAIL & STATUS UPDATE
# ─────────────────────────────────────────────────────────────────────────────
with tab_detail:
    section_header("View & Update Repair Task")

    # Quick-pick from recent tasks
    recent_tasks = get_repair_tasks(limit=20)
    if recent_tasks:
        quick_opts = ["— type or paste ID below —"] + [
            f"{t['id'][:8]}… | {t.get('status','?')} | {t.get('priority','?')} | {(t.get('updated_at','')[:10])}"
            for t in recent_tasks
        ]
        quick_sel = st.selectbox("Quick-select recent task", quick_opts, key="rm_quick_sel")
        if quick_sel != "— type or paste ID below —":
            idx_q = quick_opts.index(quick_sel) - 1
            prefilled_id = recent_tasks[idx_q]["id"] if 0 <= idx_q < len(recent_tasks) else ""
        else:
            prefilled_id = ""
    else:
        prefilled_id = ""

    task_id_input = st.text_input(
        "Task ID (full UUID):",
        value=prefilled_id,
        key="rm_task_id",
        placeholder="Paste full UUID from task list",
    )

    if task_id_input.strip():
        task = get_repair_task_by_id(task_id_input.strip())
        if not task:
            st.warning("Task not found. Ensure you have pasted the complete UUID.")
        else:
            # ── Task Details ─────────────────────────────────────────────────
            section_header("Task Details")
            dc1, dc2, dc3, dc4 = st.columns(4)
            dc1.metric("Status", task.get("status", "—"))
            dc2.metric("Priority", task.get("priority", "—"))
            dc3.metric("Est. Cost", f"₹{task.get('est_cost') or 0:,.0f}")
            dc4.metric("Actual Cost", f"₹{task.get('actual_cost') or 0:,.0f}")

            dd1, dd2, dd3, dd4 = st.columns(4)
            dd1.metric("Severity", task.get("severity") or "—")
            dd2.metric("Assign Team", task.get("assigned_team") or "—")
            dd3.metric("Assign Worker", task.get("assigned_worker") or "—")
            dd4.metric("Due Date", task.get("due_date") or "—")

            if task.get("source_name"):
                st.caption(f"🔗 Linked detection: {task.get('source_name', '')[:60]} | {task.get('detection_id','')[:16]}…")
            if task.get("repair_notes"):
                st.markdown(f"**Notes:** {task['repair_notes']}")

            st.markdown("---")

            # ── Status Transition ─────────────────────────────────────────────
            section_header("Update Status")
            current_status = task.get("status", "Pending Verification")
            curr_idx = VALID_STATUSES.index(current_status) if current_status in VALID_STATUSES else 0
            ua1, ua2 = st.columns(2)
            with ua1:
                new_status = st.selectbox("New status", VALID_STATUSES,
                                          index=curr_idx, key="rm_new_status")
            with ua2:
                changed_by = st.text_input("Changed by", key="rm_changed_by",
                                           placeholder="Your name or team")
            change_notes = st.text_input("Change notes (optional)", key="rm_change_notes")

            # ── Update fields ─────────────────────────────────────────────────
            section_header("Update Assignment & Cost")
            uf1, uf2, uf3, uf4 = st.columns(4)
            with uf1:
                new_team = st.text_input("Team", value=task.get("assigned_team") or "", key="rm_upd_team")
            with uf2:
                new_worker = st.text_input("Worker", value=task.get("assigned_worker") or "", key="rm_upd_worker")
            with uf3:
                actual_cost = st.number_input(
                    "Actual cost (₹)", min_value=0,
                    value=int(task.get("actual_cost") or 0), key="rm_actual_cost",
                )
            with uf4:
                new_due = st.date_input(
                    "Due date",
                    value=date.fromisoformat(task["due_date"]) if task.get("due_date") else date.today() + timedelta(days=7),
                    key="rm_upd_due",
                )
            updated_notes = st.text_area(
                "Repair notes",
                value=task.get("repair_notes") or "",
                key="rm_upd_notes", height=70,
            )

            # ── Before/After Images ────────────────────────────────────────────
            section_header("Before / After Images")
            img_c1, img_c2 = st.columns(2)
            with img_c1:
                st.markdown("**Before repair image**")
                if task.get("before_image") and Path(task["before_image"]).exists():
                    st.image(task["before_image"], caption="Before", use_container_width=True)
                before_file = st.file_uploader(
                    "Upload before image", type=["jpg", "jpeg", "png", "webp"],
                    key="rm_before_img",
                )
            with img_c2:
                st.markdown("**After repair image**")
                if task.get("after_image") and Path(task["after_image"]).exists():
                    st.image(task["after_image"], caption="After", use_container_width=True)
                after_file = st.file_uploader(
                    "Upload after image", type=["jpg", "jpeg", "png", "webp"],
                    key="rm_after_img",
                )

            # ── Save ──────────────────────────────────────────────────────────
            if st.button("💾 Save All Updates", key="rm_update", type="primary"):
                try:
                    update_fields: dict = {}

                    # Status transition
                    if new_status != current_status:
                        transition_repair_status(
                            task_id_input.strip(), new_status,
                            changed_by=changed_by.strip() or None,
                            notes=change_notes.strip() or None,
                        )

                    # Field updates
                    if actual_cost > 0:
                        update_fields["actual_cost"] = float(actual_cost)
                    if new_team.strip():
                        update_fields["assigned_team"] = new_team.strip()
                    if new_worker.strip():
                        update_fields["assigned_worker"] = new_worker.strip()
                    if new_due:
                        update_fields["due_date"] = new_due.isoformat()
                    if updated_notes.strip():
                        update_fields["repair_notes"] = updated_notes.strip()

                    # Handle image uploads
                    repair_imgs_dir = config.REPAIR_IMAGES_DIR
                    repair_imgs_dir.mkdir(parents=True, exist_ok=True)

                    if before_file:
                        bpath = repair_imgs_dir / f"before_{task_id_input[:8]}_{before_file.name}"
                        bpath.write_bytes(before_file.read())
                        update_fields["before_image"] = str(bpath)

                    if after_file:
                        apath = repair_imgs_dir / f"after_{task_id_input[:8]}_{after_file.name}"
                        apath.write_bytes(after_file.read())
                        update_fields["after_image"] = str(apath)

                    # Closure timestamp
                    if new_status in ("Closed",) and "closed_at" not in update_fields:
                        from datetime import timezone
                        update_fields["closed_at"] = __import__("datetime").datetime.now(tz=timezone.utc).isoformat()

                    if update_fields:
                        update_repair_task(task_id_input.strip(), **update_fields)

                    st.success(f"✅ Task updated → status: **{new_status}**")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")

            # ── Status History Timeline ───────────────────────────────────────
            st.markdown("---")
            section_header("Status History Timeline")
            log = get_repair_status_log(task_id_input.strip())
            if log:
                for entry in log:
                    ts = (entry.get("changed_at") or "")[:16].replace("T", " ")
                    frm = entry.get("from_status") or "—"
                    to = entry.get("to_status", "—")
                    by = entry.get("changed_by") or "system"
                    nt = entry.get("notes") or ""
                    dot_color = (
                        "#10b981" if to in ("Repaired", "Closed", "Reverified", "Verified")
                        else "#ef4444" if to == "Rejected"
                        else "#4f46e5"
                    )
                    st.markdown(
                        f'<div class="timeline-item">'
                        f'<span class="timeline-dot" style="background:{dot_color}"></span>'
                        f'<span class="timeline-content">'
                        f'<span class="timeline-time">{ts} · {by}</span><br>'
                        f'<span class="timeline-text">{frm} → '
                        f'<b style="color:#a5b4fc">{to}</b>'
                        f'{f" &nbsp;· {nt}" if nt else ""}'
                        f'</span></span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No status history yet.")
    else:
        info_box("Select a recent task above or paste a full UUID to view and update it.", kind="info")

# ── Auto-refresh ───────────────────────────────────────────────────────────────
if auto_refresh:
    st.caption(f"⏱ Auto-refreshing every 10s · Last: {time.strftime('%H:%M:%S')}")
    time.sleep(10)
    st.rerun()
