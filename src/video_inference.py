"""
video_inference.py — Frame-by-frame YOLO inference on uploaded videos.

Uses safe temporary-file handling and always releases VideoCapture /
VideoWriter in a finally block.
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Callable, Generator, Iterator, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_FOURCC_CANDIDATES = ["mp4v", "avc1", "XVID"]


def _open_video(path: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise IOError(f"OpenCV could not open video: {path}")
    return cap


def _get_video_properties(cap: cv2.VideoCapture) -> dict:
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return {
        "fps": fps if fps > 0 else None,
        "width": width,
        "height": height,
        "total_frames": total_frames,
    }


def _make_writer(
    output_path: str,
    fps: float,
    width: int,
    height: int,
) -> Optional[cv2.VideoWriter]:
    """Try each fourcc candidate in order; return the first working writer."""
    fallback_fps = fps if fps and fps > 0 else 25.0
    for fourcc_str in _FOURCC_CANDIDATES:
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        writer = cv2.VideoWriter(output_path, fourcc, fallback_fps, (width, height))
        if writer.isOpened():
            return writer
        writer.release()
    return None


def process_video(
    model,
    video_bytes: bytes,
    video_filename: str,
    conf: float = 0.45,
    iou: float = 0.45,
    imgsz: int = 800,
    max_frames: int = 200,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Tuple[Optional[str], List[dict], dict]:
    """
    Run frame-by-frame YOLO inference on *video_bytes*.

    Parameters
    ----------
    model : Ultralytics YOLO model
    video_bytes : bytes
        Raw bytes of the uploaded video file.
    video_filename : str
        Original filename (used in detection records and output naming).
    conf, iou, imgsz : float, float, int
        Inference parameters.
    max_frames : int
        Maximum number of frames to process.
    progress_callback : callable(current_frame, total_frames) | None
        Optional callback invoked after each frame.

    Returns
    -------
    output_path : str | None
        Absolute path to the annotated output video, or None on failure.
    detections : list[dict]
        One dict per bounding box per frame.
    summary : dict
        Processing statistics.
    """
    tmp_input = None
    tmp_output = None
    cap = None
    writer = None
    detections: List[dict] = []
    output_path: Optional[str] = None

    try:
        # ── Write uploaded bytes to a temp file ───────────────────────────────
        suffix = Path(video_filename).suffix or ".mp4"
        tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_input.write(video_bytes)
        tmp_input.flush()
        tmp_input.close()

        cap = _open_video(tmp_input.name)
        props = _get_video_properties(cap)
        fps = props["fps"]
        width, height = props["width"], props["height"]
        total_frames = props["total_frames"]

        if width == 0 or height == 0:
            raise ValueError("Video has zero-dimension frames; cannot process.")

        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_output.close()

        writer = _make_writer(tmp_output.name, fps or 25.0, width, height)
        if writer is None:
            logger.warning("No working VideoWriter codec found; output video will not be saved.")

        process_limit = min(max_frames, total_frames) if total_frames > 0 else max_frames
        frame_idx = 0
        start_time = time.time()

        while frame_idx < process_limit:
            ret, frame = cap.read()
            if not ret:
                break

            # ── Inference ────────────────────────────────────────────────────
            try:
                results = model.predict(
                    source=frame,
                    conf=conf,
                    iou=iou,
                    imgsz=imgsz,
                    verbose=False,
                )
            except Exception as exc:
                logger.warning("Inference failed on frame %d: %s", frame_idx, exc)
                frame_idx += 1
                continue

            result = results[0]
            annotated = result.plot()

            if writer is not None:
                writer.write(annotated)

            # ── Collect detections ───────────────────────────────────────────
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                timestamp: Optional[float] = None
                if fps and fps > 0:
                    timestamp = round(frame_idx / fps, 3)

                for xyxy, conf_val, cls_id in zip(
                    boxes.xyxy.tolist(),
                    boxes.conf.tolist(),
                    boxes.cls.tolist(),
                ):
                    x1, y1, x2, y2 = xyxy
                    class_id = int(cls_id)
                    try:
                        class_name = model.names[class_id]
                    except (KeyError, AttributeError):
                        class_name = "pothole"

                    detections.append(
                        {
                            "source_video": video_filename,
                            "frame_index": frame_idx,
                            "timestamp_s": timestamp if timestamp is not None else "N/A",
                            "class_id": class_id,
                            "class_name": class_name,
                            "confidence": round(float(conf_val), 4),
                            "x1": max(0, int(x1)),
                            "y1": max(0, int(y1)),
                            "x2": min(width, int(x2)),
                            "y2": min(height, int(y2)),
                            "frame_width": width,
                            "frame_height": height,
                        }
                    )

            frame_idx += 1
            if progress_callback:
                progress_callback(frame_idx, process_limit)

        elapsed = time.time() - start_time

        # ── Finalize output ───────────────────────────────────────────────────
        if writer is not None:
            writer.release()
            writer = None
            output_path = tmp_output.name

        summary = {
            "frames_processed": frame_idx,
            "total_detections": len(detections),
            "video_fps": fps,
            "video_width": width,
            "video_height": height,
            "processing_time_s": round(elapsed, 2),
            "conf": conf,
            "iou": iou,
            "imgsz": imgsz,
        }

        return output_path, detections, summary

    finally:
        if cap is not None:
            cap.release()
        if writer is not None:
            writer.release()
        # Clean up temp input; temp output is returned to caller
        if tmp_input is not None:
            try:
                os.unlink(tmp_input.name)
            except OSError:
                pass
