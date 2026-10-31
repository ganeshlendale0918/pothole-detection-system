# Repair Workflow Documentation

## Overview
The repair lifecycle in RoadSight Intelligence Platform tracks each pothole
from initial detection through to verified closure.

## Lifecycle States

```
Detected (in detections table)
    ↓
[Create Repair Task]
    ↓
Pending Verification  ←──────────────────────────────┐
    ↓                                                 │
Verified                                              │
    ↓                                             Rejected (terminal)
Assigned
    ↓
In Progress
    ↓
Repaired
    ↓
Reverified
    ↓
Closed (terminal)
```

Any state except Closed/Rejected can transition to Rejected.

## Valid Statuses

| Status | Meaning |
|--------|---------|
| `Pending Verification` | Task created, awaiting inspector sign-off |
| `Verified` | Inspector confirmed the pothole exists |
| `Assigned` | Repair team/worker assigned |
| `In Progress` | Repair work actively underway |
| `Repaired` | Physical repair complete, pending re-inspection |
| `Reverified` | Repair quality confirmed by inspector |
| `Closed` | Fully complete, no further action required |
| `Rejected` | Not a valid pothole, duplicate, or out of scope |

## Creating a Task

1. Navigate to **Repair Management → Create Task** tab.
2. Optionally link to a saved detection record (provides severity context).
3. Set priority (Critical / High / Medium / Low).
4. Assign team and/or individual worker (optional free-text).
5. Set due date (default: today + 7 days).
6. Enter estimated cost (pre-filled based on priority × default cost config).
7. Add notes.
8. Click **Create Repair Task**.

The task is saved to the `repair_tasks` table with status `Pending Verification`.
An initial log entry is written to `repair_status_log`.

## Updating a Task

1. Navigate to **Repair Management → Task Detail** tab.
2. Paste the full UUID from the Task List.
3. Select a new status from the dropdown.
4. Optionally fill "Changed by" and "Change notes".
5. Enter actual cost if applicable.
6. Click **Update Task**.

Every status change appends an immutable record to `repair_status_log`.

## Persistence

All task data is stored in SQLite (`data/roadintel.db`).
Changes survive application restarts. No data is stored only in session state.

## Cost Estimation Defaults

| Priority | Default Estimated Cost |
|----------|------------------------|
| Low | ₹500 |
| Medium | ₹1,500 |
| High | ₹4,000 |
| Critical | ₹10,000 |

Defaults are configurable in `config.py`.

## Overdue Detection

A task is overdue when:
- `due_date IS NOT NULL`
- `due_date < today`
- `status NOT IN ('Repaired', 'Closed', 'Rejected')`

The Executive Overview, Repair Management KPI strip, and Analytics pages all surface overdue counts.

## Database Schema

```sql
CREATE TABLE repair_tasks (
    id              TEXT PRIMARY KEY,
    detection_id    TEXT,                    -- FK → detections.id
    location_id     TEXT,                    -- FK → locations.id
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Pending Verification',
    priority        TEXT NOT NULL DEFAULT 'Medium',
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
    closed_at       TEXT
);

CREATE TABLE repair_status_log (
    id          TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL,           -- FK → repair_tasks.id
    changed_at  TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    changed_by  TEXT,
    notes       TEXT
);
```
