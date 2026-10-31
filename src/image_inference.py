"""
image_inference.py — Run YOLO inference on still images.

Keeps inference logic separate from display/UI concerns.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def validate_image(image: Image.Image, min_dim: int = 32) -> None:
    """
    Raise ValueError if the image fails basic sanity checks.

    Parameters
    ----------
    image : PIL.Image.Image
    min_dim : int
        Minimum accepted width or height in pixels.
    """
    w, h = image.size
    if w < min_dim or h < min_dim:
        raise ValueError(
            f"Image is too small ({w}×{h} px). "
            f"Minimum accepted dimension is {min_dim} px."
        )
    if image.mode not in ("RGB", "RGBA", "L"):
        raise ValueError(f"Unsupported image mode: {image.mode}")


def run_image_inference(
    model,
    image: Image.Image,
    conf: float = 0.45,
    iou: float = 0.45,
    imgsz: int = 800,
    source_name: str = "uploaded_image",
) -> Tuple[Image.Image, List[dict]]:
    """
    Run YOLO detection on *image* and return an annotated image plus
    a list of detection records.

    Parameters
    ----------
    model : Ultralytics YOLO model
    image : PIL.Image.Image
        The input image (RGB or RGBA; RGBA is converted to RGB internally).
    conf : float
        Confidence threshold.
    iou : float
        IoU / NMS threshold.
    imgsz : int
        Inference image size.
    source_name : str
        Label used in the detection records (file name shown in CSV).

    Returns
    -------
    annotated_image : PIL.Image.Image
    detections : list[dict]
        One dict per bounding box with keys:
        source, detection_index, class_id, class_name, confidence,
        x1, y1, x2, y2, image_width, image_height
    """
    if image.mode == "RGBA":
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")

    img_w, img_h = image.size

    try:
        results = model.predict(
            source=image,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            verbose=False,
        )
    except Exception as exc:
        raise RuntimeError(f"Inference failed: {exc}") from exc

    result = results[0]
    annotated_bgr = result.plot()                       # numpy BGR
    annotated_pil = Image.fromarray(annotated_bgr[..., ::-1])  # → RGB PIL

    detections: List[dict] = []
    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes
        for idx, (xyxy, conf_val, cls_id) in enumerate(
            zip(boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist())
        ):
            x1, y1, x2, y2 = xyxy
            class_id = int(cls_id)
            try:
                class_name = model.names[class_id]
            except (KeyError, AttributeError):
                class_name = "pothole"

            detections.append(
                {
                    "source": source_name,
                    "detection_index": idx,
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(float(conf_val), 4),
                    "x1": max(0, int(x1)),
                    "y1": max(0, int(y1)),
                    "x2": min(img_w, int(x2)),
                    "y2": min(img_h, int(y2)),
                    "image_width": img_w,
                    "image_height": img_h,
                }
            )

    return annotated_pil, detections
