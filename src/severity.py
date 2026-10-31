"""
severity.py — Severity classification for pothole detections.

Formula
-------
Severity is derived from two signals:
  1. Detection confidence  (model certainty)
  2. Bounding-box area ratio relative to the full image  (pothole size)

A combined score is computed and mapped to one of four severity levels.
Weights are configurable via config.py.

The formula is deterministic and transparent — it makes no claim to be a
validated road-safety prediction; it is a visual triage aid only.
"""

from __future__ import annotations

from typing import Optional, Tuple

import config

# ── Severity levels (ordered LOW → HIGH) ─────────────────────────────────────
SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]

# ── Colour palette (hex) ──────────────────────────────────────────────────────
SEVERITY_COLORS = {
    "Critical": "#ef4444",   # red-500
    "High":     "#f97316",   # orange-500
    "Medium":   "#eab308",   # yellow-500
    "Low":      "#22c55e",   # green-500
    "Unknown":  "#94a3b8",   # slate-400
}

# ── Badge text ────────────────────────────────────────────────────────────────
SEVERITY_BADGES = {
    "Critical": "🔴 Critical",
    "High":     "🟠 High",
    "Medium":   "🟡 Medium",
    "Low":      "🟢 Low",
    "Unknown":  "⚪ Unknown",
}


def compute_severity(
    confidence: float,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
    conf_weight: float = 0.55,
    area_weight: float = 0.45,
) -> Tuple[str, float]:
    """
    Classify a detection as Low / Medium / High / Critical.

    Parameters
    ----------
    confidence : float      — YOLO confidence in [0, 1]
    x1, y1, x2, y2 : int   — bounding box pixel coordinates
    image_width, image_height : int | None  — full image dimensions
    conf_weight : float     — weight for confidence component  (default 0.55)
    area_weight : float     — weight for area-ratio component  (default 0.45)

    Returns
    -------
    severity : str          — "Low" | "Medium" | "High" | "Critical"
    area_ratio : float      — box area / image area (0.0 if dims unknown)
    """
    # ── Area ratio ────────────────────────────────────────────────────────────
    if image_width and image_height and image_width > 0 and image_height > 0:
        box_area = max(0, (x2 - x1)) * max(0, (y2 - y1))
        img_area = image_width * image_height
        area_ratio = min(box_area / img_area, 1.0)
    else:
        # Unknown image size → use only confidence
        area_ratio = 0.0
        conf_weight = 1.0
        area_weight = 0.0

    # ── Combined score ────────────────────────────────────────────────────────
    # Normalise area_ratio to [0,1] using a soft cap at 20% of image area
    area_score = min(area_ratio / 0.20, 1.0)
    score = conf_weight * confidence + area_weight * area_score

    # ── Threshold mapping ─────────────────────────────────────────────────────
    if score >= config.SEVERITY_THRESHOLD_CRITICAL:
        severity = "Critical"
    elif score >= config.SEVERITY_THRESHOLD_HIGH:
        severity = "High"
    elif score >= config.SEVERITY_THRESHOLD_MEDIUM:
        severity = "Medium"
    else:
        severity = "Low"

    return severity, round(area_ratio, 6)


def classify_detections(
    detections: list,
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
) -> list:
    """
    Enrich a list of detection dicts (from run_image_inference) with
    'severity' and 'area_ratio' keys.  Returns a new list.
    """
    enriched = []
    for det in detections:
        sev, ar = compute_severity(
            confidence=det.get("confidence", 0.0),
            x1=det.get("x1", 0),
            y1=det.get("y1", 0),
            x2=det.get("x2", 0),
            y2=det.get("y2", 0),
            image_width=det.get("image_width", image_width),
            image_height=det.get("image_height", image_height),
        )
        enriched.append({**det, "severity": sev, "area_ratio": ar})
    return enriched


def severity_color(severity: Optional[str]) -> str:
    """Return the hex colour for a severity level."""
    return SEVERITY_COLORS.get(severity or "Unknown", SEVERITY_COLORS["Unknown"])


def severity_badge(severity: Optional[str]) -> str:
    """Return the emoji + text badge for a severity level."""
    return SEVERITY_BADGES.get(severity or "Unknown", SEVERITY_BADGES["Unknown"])
