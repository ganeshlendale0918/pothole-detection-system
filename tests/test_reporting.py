"""
tests/test_reporting.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporting import (
    IMAGE_DETECTION_COLUMNS,
    VIDEO_DETECTION_COLUMNS,
    build_json_summary,
    detections_to_csv_bytes,
    safe_filename,
)


# ── CSV schema ────────────────────────────────────────────────────────────────

def test_image_csv_has_required_columns():
    required = {"source", "confidence", "x1", "y1", "x2", "y2"}
    assert required.issubset(set(IMAGE_DETECTION_COLUMNS))


def test_video_csv_has_required_columns():
    required = {"source_video", "frame_index", "confidence", "x1", "y1", "x2", "y2"}
    assert required.issubset(set(VIDEO_DETECTION_COLUMNS))


# ── CSV bytes generation ──────────────────────────────────────────────────────

def _make_image_detections(n: int = 3):
    return [
        {
            "source": f"img{i}.png",
            "detection_index": i,
            "class_id": 0,
            "class_name": "pothole",
            "confidence": 0.5 + i * 0.05,
            "x1": 10 * i, "y1": 20 * i,
            "x2": 100 + i * 10, "y2": 200 + i * 10,
            "image_width": 640, "image_height": 480,
        }
        for i in range(n)
    ]


def test_csv_bytes_non_empty():
    dets = _make_image_detections(3)
    result = detections_to_csv_bytes(dets, IMAGE_DETECTION_COLUMNS)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_csv_bytes_empty_detections():
    result = detections_to_csv_bytes([], IMAGE_DETECTION_COLUMNS)
    lines = result.decode("utf-8").strip().splitlines()
    # Only header row present
    assert len(lines) == 1


def test_csv_header_matches_columns():
    dets = _make_image_detections(1)
    result = detections_to_csv_bytes(dets, IMAGE_DETECTION_COLUMNS)
    header = result.decode("utf-8").splitlines()[0]
    for col in IMAGE_DETECTION_COLUMNS:
        assert col in header


def test_csv_column_order_is_stable():
    dets = _make_image_detections(1)
    bytes1 = detections_to_csv_bytes(dets, IMAGE_DETECTION_COLUMNS)
    bytes2 = detections_to_csv_bytes(dets, IMAGE_DETECTION_COLUMNS)
    assert bytes1 == bytes2


# ── JSON summary ──────────────────────────────────────────────────────────────

def test_json_summary_is_valid_json():
    raw = build_json_summary(
        source_filename="road.jpg",
        conf=0.45,
        iou=0.45,
        imgsz=800,
        detection_count=5,
    )
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_json_summary_contains_required_keys():
    raw = build_json_summary(
        source_filename="road.jpg",
        conf=0.45,
        iou=0.45,
        imgsz=800,
        detection_count=5,
    )
    parsed = json.loads(raw)
    assert "source_filename" in parsed
    assert "detection_count" in parsed
    assert "processing_settings" in parsed
    assert "processing_timestamp_utc" in parsed


def test_json_summary_zero_detections():
    raw = build_json_summary(
        source_filename="empty.jpg",
        conf=0.9,
        iou=0.5,
        imgsz=640,
        detection_count=0,
    )
    parsed = json.loads(raw)
    assert parsed["detection_count"] == 0


def test_json_summary_with_frames():
    raw = build_json_summary(
        source_filename="video.mp4",
        conf=0.45,
        iou=0.45,
        imgsz=800,
        detection_count=12,
        frames_processed=100,
    )
    parsed = json.loads(raw)
    assert parsed.get("frames_processed") == 100


# ── Safe filename ─────────────────────────────────────────────────────────────

def test_safe_filename_simple():
    assert safe_filename("road_photo.jpg") == "road_photo.jpg"


def test_safe_filename_removes_spaces():
    result = safe_filename("my file name.png")
    assert " " not in result


def test_safe_filename_removes_slashes():
    result = safe_filename("path/to/file.png")
    assert "/" not in result
