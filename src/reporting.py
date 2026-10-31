"""
reporting.py — CSV and JSON export utilities for detection results.

All column names are deterministic and stable so downstream tools
can rely on consistent schema.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


# ── Column schemas ────────────────────────────────────────────────────────────

IMAGE_DETECTION_COLUMNS = [
    "source",
    "detection_index",
    "class_id",
    "class_name",
    "confidence",
    "x1",
    "y1",
    "x2",
    "y2",
    "image_width",
    "image_height",
]

VIDEO_DETECTION_COLUMNS = [
    "source_video",
    "frame_index",
    "timestamp_s",
    "class_id",
    "class_name",
    "confidence",
    "x1",
    "y1",
    "x2",
    "y2",
    "frame_width",
    "frame_height",
]


def detections_to_csv_bytes(detections: List[dict], columns: List[str]) -> bytes:
    """
    Serialise *detections* to CSV bytes using the given *columns* order.

    Missing keys in a detection record are written as empty strings.
    Returns bytes so they can be passed directly to st.download_button.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in detections:
        # Fill any missing columns with empty string
        writer.writerow({col: row.get(col, "") for col in columns})
    return buf.getvalue().encode("utf-8")


def build_json_summary(
    *,
    project_id: str = "AI-Based Road Pothole Detection",
    source_filename: str,
    conf: float,
    iou: float,
    imgsz: int,
    detection_count: int,
    frames_processed: Optional[int] = None,
    output_file: Optional[str] = None,
    extra: Optional[dict] = None,
) -> bytes:
    """
    Build a JSON summary of an inference run.

    Returns bytes ready for st.download_button.
    """
    summary = {
        "project_identifier": project_id,
        "source_filename": source_filename,
        "processing_settings": {
            "confidence_threshold": conf,
            "iou_threshold": iou,
            "inference_image_size": imgsz,
        },
        "processing_timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "detection_count": detection_count,
    }
    if frames_processed is not None:
        summary["frames_processed"] = frames_processed
    if output_file is not None:
        summary["output_file"] = output_file
    if extra:
        summary.update(extra)

    return json.dumps(summary, indent=2, ensure_ascii=False).encode("utf-8")


def safe_filename(name: str) -> str:
    """Return *name* with common path-unsafe characters replaced by underscores."""
    keep = set("abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789-_.")
    return "".join(c if c in keep else "_" for c in name)
