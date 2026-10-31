"""
model_loader.py — Cached YOLO model loader.

Loads the custom YOLO11n pothole-detection checkpoint from models/best.pt.
The model is never retrained here; it is only loaded from the local file.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def load_model_metadata(metadata_path: Path) -> dict:
    """Return the contents of model_metadata.json, or an empty dict if missing."""
    if metadata_path.is_file():
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read model_metadata.json: %s", exc)
    return {}


def get_model(model_path: Path):
    """
    Load and return an Ultralytics YOLO model from *model_path*.

    Raises
    ------
    FileNotFoundError
        If the checkpoint does not exist at the expected location.
    RuntimeError
        If Ultralytics raises any error during model initialisation.
    """
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found: {model_path}\n"
            "Ensure models/best.pt has been copied into the project directory."
        )

    try:
        from ultralytics import YOLO  # import here to keep module lightweight

        model = YOLO(str(model_path))
        logger.info("Loaded model from: %s", model_path)
        return model
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics is not installed.  Run:  pip install ultralytics"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to load model from {model_path}: {exc}") from exc


def get_model_info(model, metadata: dict) -> dict:
    """
    Return a summary dict with model display information.

    Combines information available in the loaded model object with the
    companion model_metadata.json so the UI can show accurate details.
    """
    info: dict = {
        "checkpoint": metadata.get("main_model", "YOLO11n custom checkpoint"),
        "class_names": metadata.get("class_names", ["pothole"]),
        "inference_image_size": metadata.get("inference_image_size", 800),
        "default_confidence": metadata.get("default_confidence", 0.45),
        "default_iou": metadata.get("default_iou", 0.45),
        "status": "loaded",
    }

    # Try to read actual names from the model object
    try:
        if hasattr(model, "names") and model.names:
            info["class_names"] = list(model.names.values())
    except Exception:
        pass

    return info
