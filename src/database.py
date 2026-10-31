"""
database.py — SQLite data layer for the RoadSight Intelligence Platform.

Uses only Python stdlib `sqlite3` — no additional dependencies.
All tables use CREATE TABLE IF NOT EXISTS, so the DB is self-migrating.

Schema
------
detections          — every saved inference result (image or video frame)
locations           — optional GPS / user-entered coordinates linked to detections
repair_tasks        — lifecycle: Detected → Verified → Assigned → In Progress → Repaired → Closed
repair_status_log   — immutable audit trail of every status change
simulation_runs     — metadata for simulation scenario runs (isolated)
simulation_records  — simulated pothole records (never shown in real dashboards)
app_settings        — key-value persistent settings
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import config

logger = logging.getLogger(__name__)

DB_PATH: Path = config.DB_PATH


# ─────────────────────────────────────────────────────────────────────────────
# Connection helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Open (or create) the SQLite database and return a connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """Context manager: yields a connection and commits/rolls back automatically."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Schema initialisation
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS detections (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    source_name     TEXT NOT NULL,
    source_type     TEXT NOT NULL DEFAULT 'image',   -- 'image' | 'video' | 'demo'
    detection_index INTEGER NOT NULL DEFAULT 0,
    class_id        INTEGER NOT NULL DEFAULT 0,
    class_name      TEXT NOT NULL DEFAULT 'pothole',
    confidence      REAL NOT NULL,
    x1              INTEGER NOT NULL,
    y1              INTEGER NOT NULL,
    x2              INTEGER NOT NULL,
    y2              INTEGER NOT NULL,
    image_width     INTEGER,
    image_height    INTEGER,
    frame_index     INTEGER,
    timestamp_s     REAL,
    conf_threshold  REAL,
    iou_threshold   REAL,
    imgsz           INTEGER,
    severity        TEXT,                            -- Low | Medium | High | Critical
    area_ratio      REAL,
    notes           TEXT,
    annotated_path  TEXT
);

CREATE TABLE IF NOT EXISTS locations (
    id              TEXT PRIMARY KEY,
    detection_id    TEXT,
    created_at      TEXT NOT NULL,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    address         TEXT,
    location_source TEXT NOT NULL DEFAULT 'manual',  -- 'manual' | 'map_click' | 'geocoded' | 'gps'
    area_name       TEXT,
    notes           TEXT,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS repair_tasks (
    id              TEXT PRIMARY KEY,
    detection_id    TEXT,
    location_id     TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Pending Verification',
    priority        TEXT NOT NULL DEFAULT 'Medium',  -- Low | Medium | High | Critical
    assigned_team   TEXT,
    assigned_worker TEXT,
    due_date        TEXT,
    est_cost        REAL,
    actual_cost     REAL,
    before_image    TEXT,
    after_image     TEXT,
    repair_notes    TEXT,
    verified_by     TEXT,
    verified_at     TEXT,
    closed_at       TEXT,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE SET NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS repair_status_log (
    id              TEXT PRIMARY KEY,
    task_id         TEXT NOT NULL,
    changed_at      TEXT NOT NULL,
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    changed_by      TEXT,
    notes           TEXT,
    FOREIGN KEY (task_id) REFERENCES repair_tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulation_runs (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    config_json     TEXT,
    result_summary  TEXT
);

CREATE TABLE IF NOT EXISTS simulation_records (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    lat             REAL,
    lon             REAL,
    severity        TEXT,
    status          TEXT,
    est_cost        REAL,
    days_to_repair  INTEGER,
    area_name       TEXT,
    FOREIGN KEY (run_id) REFERENCES simulation_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_detections_created  ON detections(created_at);
CREATE INDEX IF NOT EXISTS idx_detections_severity ON detections(severity);
CREATE INDEX IF NOT EXISTS idx_locations_detection ON locations(detection_id);
CREATE INDEX IF NOT EXISTS idx_repair_detection    ON repair_tasks(detection_id);
CREATE INDEX IF NOT EXISTS idx_repair_status       ON repair_tasks(status);
CREATE INDEX IF NOT EXISTS idx_sim_records_run     ON simulation_records(run_id);
"""


def init_db() -> None:
    """Create all tables and indexes if they don't already exist."""
    with db_conn() as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("Database initialised at %s", DB_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now_utc() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ─────────────────────────────────────────────────────────────────────────────
# Detections
# ─────────────────────────────────────────────────────────────────────────────

def save_detection(
    *,
    source_name: str,
    source_type: str = "image",
    detection_index: int = 0,
    class_id: int = 0,
    class_name: str = "pothole",
    confidence: float,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
    frame_index: Optional[int] = None,
    timestamp_s: Optional[float] = None,
    conf_threshold: Optional[float] = None,
    iou_threshold: Optional[float] = None,
    imgsz: Optional[int] = None,
    severity: Optional[str] = None,
    area_ratio: Optional[float] = None,
    notes: Optional[str] = None,
    annotated_path: Optional[str] = None,
) -> str:
    """Insert a detection record and return its UUID."""
    rec_id = _new_id()
    now = _now_utc()
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO detections
               (id, created_at, source_name, source_type, detection_index,
                class_id, class_name, confidence, x1, y1, x2, y2,
                image_width, image_height, frame_index, timestamp_s,
                conf_threshold, iou_threshold, imgsz, severity, area_ratio,
                notes, annotated_path)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rec_id, now, source_name, source_type, detection_index,
             class_id, class_name, confidence, x1, y1, x2, y2,
             image_width, image_height, frame_index, timestamp_s,
             conf_threshold, iou_threshold, imgsz, severity, area_ratio,
             notes, annotated_path),
        )
    return rec_id


def save_detections_batch(records: List[dict]) -> List[str]:
    """Insert multiple detection records in one transaction. Returns list of IDs."""
    ids = []
    now = _now_utc()
    with db_conn() as conn:
        for r in records:
            rec_id = _new_id()
            ids.append(rec_id)
            conn.execute(
                """INSERT INTO detections
                   (id, created_at, source_name, source_type, detection_index,
                    class_id, class_name, confidence, x1, y1, x2, y2,
                    image_width, image_height, frame_index, timestamp_s,
                    conf_threshold, iou_threshold, imgsz, severity, area_ratio,
                    notes, annotated_path)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rec_id, now,
                 r.get("source_name", r.get("source", "unknown")),
                 r.get("source_type", "image"),
                 r.get("detection_index", 0),
                 r.get("class_id", 0),
                 r.get("class_name", "pothole"),
                 r["confidence"],
                 r["x1"], r["y1"], r["x2"], r["y2"],
                 r.get("image_width"), r.get("image_height"),
                 r.get("frame_index"), r.get("timestamp_s"),
                 r.get("conf_threshold"), r.get("iou_threshold"),
                 r.get("imgsz"),
                 r.get("severity"), r.get("area_ratio"),
                 r.get("notes"), r.get("annotated_path")),
            )
    return ids


def get_detections(
    *,
    limit: int = 200,
    offset: int = 0,
    severity: Optional[str] = None,
    source_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
) -> List[dict]:
    """Return detection records, newest first, with optional filters."""
    clauses = ["1=1"]
    params: List[Any] = []
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    if source_type:
        clauses.append("source_type = ?")
        params.append(source_type)
    if date_from:
        clauses.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("created_at <= ?")
        params.append(date_to + "T23:59:59")
    if search:
        clauses.append("(source_name LIKE ? OR notes LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    sql = f"""
        SELECT * FROM detections
        WHERE {' AND '.join(clauses)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with db_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def count_detections(**filters) -> int:
    """Return total count matching the same filters as get_detections."""
    clauses = ["1=1"]
    params: List[Any] = []
    severity = filters.get("severity")
    source_type = filters.get("source_type")
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")
    if severity:
        clauses.append("severity = ?"); params.append(severity)
    if source_type:
        clauses.append("source_type = ?"); params.append(source_type)
    if date_from:
        clauses.append("created_at >= ?"); params.append(date_from)
    if date_to:
        clauses.append("created_at <= ?"); params.append(date_to + "T23:59:59")
    sql = f"SELECT COUNT(*) FROM detections WHERE {' AND '.join(clauses)}"
    with db_conn() as conn:
        return conn.execute(sql, params).fetchone()[0]


def get_detection_by_id(det_id: str) -> Optional[dict]:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM detections WHERE id=?", (det_id,)).fetchone()
    return _row_to_dict(row) if row else None


def delete_detection(det_id: str) -> None:
    with db_conn() as conn:
        conn.execute("DELETE FROM detections WHERE id=?", (det_id,))


def get_kpi_summary() -> dict:
    """Return aggregate KPIs for the Executive Overview."""
    with db_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        today = datetime.now(tz=timezone.utc).date().isoformat()
        today_count = conn.execute(
            "SELECT COUNT(*) FROM detections WHERE created_at >= ?", (today,)
        ).fetchone()[0]
        sev_rows = conn.execute(
            "SELECT severity, COUNT(*) as cnt FROM detections GROUP BY severity"
        ).fetchall()
        severity_dist = {r["severity"] or "Unknown": r["cnt"] for r in sev_rows}
        high_sev = severity_dist.get("Critical", 0) + severity_dist.get("High", 0)

        repair_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM repair_tasks GROUP BY status"
        ).fetchall()
        repair_dist = {r["status"]: r["cnt"] for r in repair_rows}

        repaired = repair_dist.get("Repaired", 0) + repair_dist.get("Closed", 0)
        in_progress = repair_dist.get("In Progress", 0)
        pending_verif = repair_dist.get("Pending Verification", 0)
        total_tasks = sum(repair_dist.values())
        completion_pct = round(repaired / max(total_tasks, 1) * 100, 1)

        est_cost_row = conn.execute(
            "SELECT SUM(est_cost) FROM repair_tasks WHERE est_cost IS NOT NULL"
        ).fetchone()[0]

    return {
        "total_detections": total,
        "today_detections": today_count,
        "high_severity": high_sev,
        "pending_verification": pending_verif,
        "repairs_in_progress": in_progress,
        "repaired": repaired,
        "repair_completion_pct": completion_pct,
        "total_repair_tasks": total_tasks,
        "est_total_cost": est_cost_row or 0.0,
        "severity_distribution": severity_dist,
        "repair_status_distribution": repair_dist,
    }


def get_detection_timeline(days: int = 30) -> List[dict]:
    """Return daily detection counts for the past N days."""
    with db_conn() as conn:
        rows = conn.execute(
            """
            SELECT substr(created_at, 1, 10) as day, COUNT(*) as count
            FROM detections
            WHERE created_at >= datetime('now', ?)
            GROUP BY day ORDER BY day
            """,
            (f"-{days} days",),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Locations
# ─────────────────────────────────────────────────────────────────────────────

def save_location(
    *,
    lat: float,
    lon: float,
    detection_id: Optional[str] = None,
    address: Optional[str] = None,
    location_source: str = "manual",
    area_name: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    loc_id = _new_id()
    now = _now_utc()
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO locations
               (id, detection_id, created_at, lat, lon, address,
                location_source, area_name, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (loc_id, detection_id, now, lat, lon, address,
             location_source, area_name, notes),
        )
    return loc_id


def get_locations(
    *,
    severity_filter: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[dict]:
    """Return locations joined with their detection (for map rendering)."""
    clauses = ["1=1"]
    params: List[Any] = []
    if date_from:
        clauses.append("l.created_at >= ?"); params.append(date_from)
    if date_to:
        clauses.append("l.created_at <= ?"); params.append(date_to + "T23:59:59")
    if severity_filter:
        placeholders = ",".join("?" * len(severity_filter))
        clauses.append(f"d.severity IN ({placeholders})")
        params.extend(severity_filter)

    sql = f"""
        SELECT l.id, l.detection_id, l.lat, l.lon, l.address,
               l.location_source, l.area_name, l.notes, l.created_at,
               d.confidence, d.severity, d.source_name, d.source_type
        FROM locations l
        LEFT JOIN detections d ON d.id = l.detection_id
        WHERE {' AND '.join(clauses)}
        ORDER BY l.created_at DESC
    """
    with db_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_location_by_id(loc_id: str) -> Optional[dict]:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM locations WHERE id=?", (loc_id,)).fetchone()
    return _row_to_dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
# Repair tasks
# ─────────────────────────────────────────────────────────────────────────────

VALID_STATUSES = [
    "Pending Verification",
    "Verified",
    "Assigned",
    "In Progress",
    "Repaired",
    "Reverified",
    "Closed",
    "Rejected",
]


def create_repair_task(
    *,
    detection_id: Optional[str] = None,
    location_id: Optional[str] = None,
    priority: str = "Medium",
    assigned_team: Optional[str] = None,
    assigned_worker: Optional[str] = None,
    due_date: Optional[str] = None,
    est_cost: Optional[float] = None,
    repair_notes: Optional[str] = None,
) -> str:
    task_id = _new_id()
    now = _now_utc()
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO repair_tasks
               (id, detection_id, location_id, created_at, updated_at,
                status, priority, assigned_team, assigned_worker, due_date,
                est_cost, repair_notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (task_id, detection_id, location_id, now, now,
             "Pending Verification", priority, assigned_team, assigned_worker,
             due_date, est_cost, repair_notes),
        )
        # Log initial status
        conn.execute(
            """INSERT INTO repair_status_log
               (id, task_id, changed_at, from_status, to_status, notes)
               VALUES (?,?,?,?,?,?)""",
            (_new_id(), task_id, now, None, "Pending Verification", "Task created"),
        )
    return task_id


def update_repair_task(task_id: str, **fields) -> None:
    """Update arbitrary fields on a repair task."""
    if not fields:
        return
    allowed = {
        "status", "priority", "assigned_team", "assigned_worker", "due_date",
        "est_cost", "actual_cost", "before_image", "after_image", "repair_notes",
        "verified_by", "verified_at", "closed_at",
    }
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return
    safe["updated_at"] = _now_utc()
    set_clause = ", ".join(f"{k}=?" for k in safe)
    values = list(safe.values()) + [task_id]
    with db_conn() as conn:
        conn.execute(f"UPDATE repair_tasks SET {set_clause} WHERE id=?", values)


def transition_repair_status(
    task_id: str,
    new_status: str,
    changed_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> None:
    """Change status + append an audit log entry."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status!r}. Valid: {VALID_STATUSES}")
    now = _now_utc()
    with db_conn() as conn:
        row = conn.execute(
            "SELECT status FROM repair_tasks WHERE id=?", (task_id,)
        ).fetchone()
        if not row:
            raise KeyError(f"Repair task not found: {task_id}")
        old_status = row["status"]
        conn.execute(
            "UPDATE repair_tasks SET status=?, updated_at=? WHERE id=?",
            (new_status, now, task_id),
        )
        extra_fields: dict = {}
        if new_status == "Closed":
            extra_fields["closed_at"] = now
        if extra_fields:
            set_clause = ", ".join(f"{k}=?" for k in extra_fields)
            conn.execute(
                f"UPDATE repair_tasks SET {set_clause} WHERE id=?",
                list(extra_fields.values()) + [task_id],
            )
        conn.execute(
            """INSERT INTO repair_status_log
               (id, task_id, changed_at, from_status, to_status, changed_by, notes)
               VALUES (?,?,?,?,?,?,?)""",
            (_new_id(), task_id, now, old_status, new_status, changed_by, notes),
        )


def get_repair_tasks(
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[dict]:
    clauses = ["1=1"]
    params: List[Any] = []
    if status:
        clauses.append("rt.status = ?"); params.append(status)
    if priority:
        clauses.append("rt.priority = ?"); params.append(priority)
    sql = f"""
        SELECT rt.*, d.source_name, d.confidence, d.severity,
               l.lat, l.lon, l.area_name, l.address
        FROM repair_tasks rt
        LEFT JOIN detections d ON d.id = rt.detection_id
        LEFT JOIN locations  l ON l.id = rt.location_id
        WHERE {' AND '.join(clauses)}
        ORDER BY rt.updated_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with db_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_repair_task_by_id(task_id: str) -> Optional[dict]:
    with db_conn() as conn:
        row = conn.execute(
            """SELECT rt.*, d.source_name, d.confidence, d.severity,
                      l.lat, l.lon, l.area_name
               FROM repair_tasks rt
               LEFT JOIN detections d ON d.id = rt.detection_id
               LEFT JOIN locations  l ON l.id = rt.location_id
               WHERE rt.id=?""",
            (task_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_repair_status_log(task_id: str) -> List[dict]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM repair_status_log WHERE task_id=? ORDER BY changed_at",
            (task_id,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_repair_kpis() -> dict:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM repair_tasks GROUP BY status"
        ).fetchall()
        dist = {r["status"]: r["cnt"] for r in rows}
        cost_row = conn.execute(
            "SELECT SUM(est_cost) as est, SUM(actual_cost) as actual FROM repair_tasks"
        ).fetchone()
        overdue_count = conn.execute(
            """SELECT COUNT(*) FROM repair_tasks
               WHERE due_date IS NOT NULL
                 AND due_date < date('now')
                 AND status NOT IN ('Repaired','Closed','Rejected')"""
        ).fetchone()[0]
    total = sum(dist.values())
    repaired = dist.get("Repaired", 0) + dist.get("Closed", 0)
    return {
        "status_distribution": dist,
        "total_tasks": total,
        "repaired": repaired,
        "completion_pct": round(repaired / max(total, 1) * 100, 1),
        "overdue": overdue_count,
        "est_total_cost": cost_row["est"] or 0.0,
        "actual_total_cost": cost_row["actual"] or 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Simulation
# ─────────────────────────────────────────────────────────────────────────────

def save_simulation_run(
    name: str,
    description: str,
    config_dict: dict,
    result_summary: dict,
    records: List[dict],
) -> str:
    run_id = _new_id()
    now = _now_utc()
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO simulation_runs
               (id, created_at, name, description, config_json, result_summary)
               VALUES (?,?,?,?,?,?)""",
            (run_id, now, name, description,
             json.dumps(config_dict), json.dumps(result_summary)),
        )
        for r in records:
            conn.execute(
                """INSERT INTO simulation_records
                   (id, run_id, created_at, lat, lon, severity, status,
                    est_cost, days_to_repair, area_name)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (_new_id(), run_id, now,
                 r.get("lat"), r.get("lon"),
                 r.get("severity"), r.get("status", "Simulated"),
                 r.get("est_cost"), r.get("days_to_repair"),
                 r.get("area_name")),
            )
    return run_id


def get_simulation_runs() -> List[dict]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM simulation_runs ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_simulation_records(run_id: str) -> List[dict]:
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM simulation_records WHERE run_id=?", (run_id,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def delete_simulation_run(run_id: str) -> None:
    with db_conn() as conn:
        conn.execute("DELETE FROM simulation_runs WHERE id=?", (run_id,))


# ─────────────────────────────────────────────────────────────────────────────
# App Settings
# ─────────────────────────────────────────────────────────────────────────────

def get_setting(key: str, default: Any = None) -> Any:
    with db_conn() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key=?", (key,)
        ).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return row["value"]


def set_setting(key: str, value: Any) -> None:
    now = _now_utc()
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO app_settings(key, value, updated_at)
               VALUES (?,?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, json.dumps(value), now),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Analytics helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_analytics_data() -> dict:
    """Return all data needed for the analytics dashboard."""
    with db_conn() as conn:
        daily = [_row_to_dict(r) for r in conn.execute(
            """SELECT substr(created_at,1,10) as day,
                      COUNT(*) as total,
                      SUM(CASE WHEN severity='Critical' THEN 1 ELSE 0 END) as critical,
                      SUM(CASE WHEN severity='High' THEN 1 ELSE 0 END) as high,
                      SUM(CASE WHEN severity='Medium' THEN 1 ELSE 0 END) as medium,
                      SUM(CASE WHEN severity='Low' THEN 1 ELSE 0 END) as low
               FROM detections
               GROUP BY day ORDER BY day DESC LIMIT 90"""
        ).fetchall()]

        conf_dist = [_row_to_dict(r) for r in conn.execute(
            "SELECT confidence FROM detections ORDER BY confidence"
        ).fetchall()]

        area_dist = [_row_to_dict(r) for r in conn.execute(
            """SELECT l.area_name, COUNT(*) as count
               FROM locations l
               JOIN detections d ON d.id = l.detection_id
               WHERE l.area_name IS NOT NULL
               GROUP BY l.area_name ORDER BY count DESC LIMIT 20"""
        ).fetchall()]

        source_dist = [_row_to_dict(r) for r in conn.execute(
            "SELECT source_name, COUNT(*) as cnt FROM detections GROUP BY source_name ORDER BY cnt DESC LIMIT 20"
        ).fetchall()]

        repair_trend = [_row_to_dict(r) for r in conn.execute(
            """SELECT substr(updated_at,1,10) as day, status, COUNT(*) as cnt
               FROM repair_tasks GROUP BY day, status ORDER BY day DESC LIMIT 90"""
        ).fetchall()]

        cost_data = [_row_to_dict(r) for r in conn.execute(
            """SELECT id, est_cost, actual_cost, status, priority
               FROM repair_tasks WHERE est_cost IS NOT NULL"""
        ).fetchall()]

    return {
        "daily_detections": daily,
        "confidence_values": [r["confidence"] for r in conf_dist],
        "area_distribution": area_dist,
        "source_distribution": source_dist,
        "repair_trend": repair_trend,
        "cost_data": cost_data,
    }


# Initialise on import
try:
    init_db()
except Exception as _e:
    logger.error("Failed to initialise database: %s", _e)
