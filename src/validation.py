"""
validation.py — Input validation helpers shared by app and tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


ACCEPTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ACCEPTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


def is_accepted_image(filename: str) -> bool:
    """Return True if *filename* has an accepted image extension."""
    return Path(filename).suffix.lower() in ACCEPTED_IMAGE_EXTENSIONS


def is_accepted_video(filename: str) -> bool:
    """Return True if *filename* has an accepted video extension."""
    return Path(filename).suffix.lower() in ACCEPTED_VIDEO_EXTENSIONS


def validate_model_path(path: Path) -> None:
    """
    Raise FileNotFoundError if the model checkpoint is absent.

    Parameters
    ----------
    path : Path
        Expected location of the .pt checkpoint.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found at: {path}\n"
            "Copy models/best.pt into the project before running the app."
        )
    if path.suffix.lower() != ".pt":
        raise ValueError(f"Expected a .pt checkpoint file, got: {path.name}")


def validate_detection_record(record: dict) -> List[str]:
    """
    Return a list of validation error strings for *record*.

    An empty list means the record is valid.
    """
    errors: List[str] = []
    required_keys = {"confidence", "x1", "y1", "x2", "y2"}
    for key in required_keys:
        if key not in record:
            errors.append(f"Missing required key: '{key}'")

    if "confidence" in record:
        c = record["confidence"]
        if not isinstance(c, (int, float)) or not (0.0 <= float(c) <= 1.0):
            errors.append(f"confidence must be in [0, 1], got: {c!r}")

    for coord in ("x1", "y1", "x2", "y2"):
        if coord in record and not isinstance(record[coord], (int, float)):
            errors.append(f"{coord} must be numeric, got: {record[coord]!r}")

    if {"x1", "x2"} <= record.keys():
        if record["x1"] > record["x2"]:
            errors.append(f"x1 ({record['x1']}) must be <= x2 ({record['x2']})")

    if {"y1", "y2"} <= record.keys():
        if record["y1"] > record["y2"]:
            errors.append(f"y1 ({record['y1']}) must be <= y2 ({record['y2']})")

    return errors
