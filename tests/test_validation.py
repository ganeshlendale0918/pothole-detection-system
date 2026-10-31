"""
tests/test_validation.py
"""

import sys
from pathlib import Path

# Make src importable without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation import (
    is_accepted_image,
    is_accepted_video,
    validate_model_path,
    validate_detection_record,
)


# ── File-extension checks ─────────────────────────────────────────────────────

def test_accepted_image_jpg():
    assert is_accepted_image("photo.jpg") is True


def test_accepted_image_png():
    assert is_accepted_image("road.PNG") is True


def test_accepted_image_webp():
    assert is_accepted_image("cam.webp") is True


def test_rejected_image_txt():
    assert is_accepted_image("notes.txt") is False


def test_rejected_image_exe():
    assert is_accepted_image("malware.exe") is False


def test_accepted_video_mp4():
    assert is_accepted_video("clip.mp4") is True


def test_accepted_video_avi():
    assert is_accepted_video("footage.AVI") is True


def test_rejected_video_jpg():
    assert is_accepted_video("frame.jpg") is False


# ── Model path validation ─────────────────────────────────────────────────────

def test_validate_model_path_missing(tmp_path):
    import pytest
    fake = tmp_path / "nonexistent.pt"
    with pytest.raises(FileNotFoundError):
        validate_model_path(fake)


def test_validate_model_path_wrong_extension(tmp_path):
    import pytest
    wrong = tmp_path / "model.onnx"
    wrong.write_bytes(b"dummy")
    with pytest.raises(ValueError):
        validate_model_path(wrong)


# ── Detection record validation ───────────────────────────────────────────────

def _good_record():
    return {
        "confidence": 0.75,
        "x1": 10, "y1": 20,
        "x2": 100, "y2": 200,
    }


def test_valid_record_no_errors():
    assert validate_detection_record(_good_record()) == []


def test_invalid_confidence_above_one():
    rec = _good_record()
    rec["confidence"] = 1.5
    errors = validate_detection_record(rec)
    assert any("confidence" in e for e in errors)


def test_invalid_confidence_negative():
    rec = _good_record()
    rec["confidence"] = -0.1
    errors = validate_detection_record(rec)
    assert any("confidence" in e for e in errors)


def test_missing_confidence_key():
    rec = _good_record()
    del rec["confidence"]
    errors = validate_detection_record(rec)
    assert any("confidence" in e for e in errors)


def test_x1_greater_than_x2():
    rec = _good_record()
    rec["x1"] = 200
    rec["x2"] = 50
    errors = validate_detection_record(rec)
    assert any("x1" in e for e in errors)


def test_y1_greater_than_y2():
    rec = _good_record()
    rec["y1"] = 300
    rec["y2"] = 100
    errors = validate_detection_record(rec)
    assert any("y1" in e for e in errors)
