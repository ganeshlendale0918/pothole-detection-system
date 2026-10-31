"""
risk_score.py — Area-level road risk scoring for the Road Condition Intelligence page.

Risk Score Formula
------------------
Risk is computed per geographic area (area_name cluster or grid cell) using:

    R = w1 * norm(pothole_count)
      + w2 * norm(avg_severity_value)
      + w3 * norm(recurrence_rate)
      + w4 * norm(age_days_unresolved)

Where:
  - pothole_count     : number of real (non-simulated) detections in the area
  - avg_severity_value: mean severity mapped to numeric (Low=1, Medium=2, High=3, Critical=4)
  - recurrence_rate   : fraction of sources detected more than once in the area
  - age_days_unresolved: average age (days) of un-repaired detections

All inputs are normalised to [0, 1] relative to the maximum observed value
across all areas before weighting.

Default weights and thresholds are configurable.

DISCLAIMER: This score is a visual prioritisation aid, not a validated
road-safety prediction.  It should be used to guide inspection priorities only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

import config

_SEVERITY_NUMERIC: Dict[str, float] = {
    "Low": 1.0,
    "Medium": 2.0,
    "High": 3.0,
    "Critical": 4.0,
}


def _days_since(iso_ts: str) -> float:
    """Return elapsed days since an ISO-8601 UTC timestamp."""
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        now = datetime.now(tz=timezone.utc)
        return max(0.0, (now - ts).total_seconds() / 86400)
    except Exception:
        return 0.0


def _norm(values: List[float]) -> List[float]:
    """Min-max normalise a list of floats to [0, 1].  All-zero → all-zero."""
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.0] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def compute_area_risk_scores(
    detections: List[dict],
    repair_tasks: Optional[List[dict]] = None,
    *,
    w_count: float = 0.30,
    w_severity: float = 0.30,
    w_recurrence: float = 0.20,
    w_age: float = 0.20,
) -> List[dict]:
    """
    Compute risk scores for each area present in *detections*.

    Parameters
    ----------
    detections : list[dict]
        Real detection records from the database (must have 'area_name' or
        derived from location join, or 'source_name').
    repair_tasks : list[dict] | None
        Repair task records (used to skip repaired/closed detections from
        the age calculation).
    w_count, w_severity, w_recurrence, w_age : float
        Weights; must sum to ~1.0 (not enforced, but normalised internally).

    Returns
    -------
    list[dict] sorted by risk_score descending, each with keys:
        area_name, pothole_count, avg_severity, recurrence_rate,
        avg_age_days, risk_score, risk_label
    """
    if not detections:
        return []

    repaired_detection_ids: set = set()
    if repair_tasks:
        for t in repair_tasks:
            if t.get("status") in ("Repaired", "Closed") and t.get("detection_id"):
                repaired_detection_ids.add(t["detection_id"])

    # Group detections by area
    area_groups: Dict[str, List[dict]] = {}
    for d in detections:
        area = d.get("area_name") or d.get("source_name", "Unknown Area")
        area_groups.setdefault(area, []).append(d)

    raw: List[dict] = []
    for area, dets in area_groups.items():
        count = len(dets)
        sev_values = [
            _SEVERITY_NUMERIC.get(d.get("severity", "Low"), 1.0) for d in dets
        ]
        avg_severity = sum(sev_values) / len(sev_values)

        # Recurrence: areas where the same source_name appears >1 detection
        sources = [d.get("source_name", "") for d in dets]
        source_counts: Dict[str, int] = {}
        for s in sources:
            source_counts[s] = source_counts.get(s, 0) + 1
        recurring = sum(1 for c in source_counts.values() if c > 1)
        recurrence_rate = recurring / max(len(source_counts), 1)

        # Age of unresolved detections
        unresolved_ages = []
        for d in dets:
            if d.get("id") not in repaired_detection_ids:
                unresolved_ages.append(_days_since(d.get("created_at", "")))
        avg_age = sum(unresolved_ages) / len(unresolved_ages) if unresolved_ages else 0.0

        raw.append({
            "area_name": area,
            "pothole_count": count,
            "_avg_severity_val": avg_severity,
            "avg_severity": _numeric_to_label(avg_severity),
            "recurrence_rate": round(recurrence_rate, 3),
            "avg_age_days": round(avg_age, 1),
            "_sev_raw": avg_severity,
        })

    if not raw:
        return []

    # Normalise each component across all areas
    counts_norm = _norm([r["pothole_count"] for r in raw])
    sev_norm = _norm([r["_avg_severity_val"] for r in raw])
    recur_norm = _norm([r["recurrence_rate"] for r in raw])
    age_norm = _norm([r["avg_age_days"] for r in raw])

    total_w = w_count + w_severity + w_recurrence + w_age

    results = []
    for i, r in enumerate(raw):
        score = (
            w_count * counts_norm[i]
            + w_severity * sev_norm[i]
            + w_recurrence * recur_norm[i]
            + w_age * age_norm[i]
        ) / total_w
        score = round(min(score, 1.0) * 100, 1)  # 0–100 scale
        results.append({
            "area_name": r["area_name"],
            "pothole_count": r["pothole_count"],
            "avg_severity": r["avg_severity"],
            "recurrence_rate": r["recurrence_rate"],
            "avg_age_days": r["avg_age_days"],
            "risk_score": score,
            "risk_label": _risk_label(score),
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


def _numeric_to_label(val: float) -> str:
    if val >= 3.5:
        return "Critical"
    elif val >= 2.5:
        return "High"
    elif val >= 1.5:
        return "Medium"
    return "Low"


def _risk_label(score: float) -> str:
    if score >= 75:
        return "⚠️ Very High Risk"
    elif score >= 50:
        return "🔶 High Risk"
    elif score >= 25:
        return "🟡 Moderate Risk"
    return "🟢 Low Risk"
