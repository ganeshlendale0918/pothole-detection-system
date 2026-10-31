"""
2_Live_Detection.py — Live Detection Center for RoadSight Intelligence Platform.
Preserves all existing YOLO11n inference logic. Adds: severity classification,
DB persistence, side-by-side comparison, FPS measurement, location linking.
"""

from __future__ import annotations

import io
import os
import sys
import time
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.model_loader import get_model, get_model_info, load_model_metadata
from src.validation import validate_model_path, is_accepted_image, is_accepted_video
from src.image_inference import run_image_inference, validate_image
from src.video_inference import process_video
from src.reporting import (
    IMAGE_DETECTION_COLUMNS, VIDEO_DETECTION_COLUMNS,
    build_json_summary, detections_to_csv_bytes, safe_filename,
)
from src.severity import classify_detections, severity_badge, SEVERITY_COLORS
from src.database import save_detections_batch, save_location, init_db
from src.ui_components import (
    inject_css, hero_banner, section_header, info_box, metric_row,
    severity_pill, empty_state,
)

st.set_page_config(page_title="Live Detection · RoadSight", page_icon="🔍", layout="wide")
init_db()
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div class="sidebar-logo"><h2>🛣️ RoadSight</h2><p>Intelligence Platform v2.0</p></div>""",
                unsafe_allow_html=True)

    # Load model (reuse cached if available)
    @st.cache_resource(show_spinner="Loading YOLO11n…")
    def _load():
        validate_model_path(config.DEFAULT_MODEL_PATH)
        meta  = load_model_metadata(config.MODEL_METADATA_PATH)
        mdl   = get_model(config.DEFAULT_MODEL_PATH)
        info  = get_model_info(mdl, meta)
        return mdl, info

    try:
        model, model_info = _load()
        model_error = None
        st.markdown('<span class="status-ok">✓ YOLO11n Loaded</span>', unsafe_allow_html=True)
        st.caption(model_info.get("checkpoint", ""))
    except Exception as exc:
        model, model_info, model_error = None, {}, str(exc)
        st.markdown('<span class="status-err">⚠ Model unavailable</span>', unsafe_allow_html=True)
        st.caption(str(exc)[:200])

    st.markdown("---")
    st.markdown("### ⚙️ Inference Settings")
    default_conf = model_info.get("default_confidence", config.DEFAULT_CONF) if model_info else config.DEFAULT_CONF
    default_iou  = model_info.get("default_iou", config.DEFAULT_IOU) if model_info else config.DEFAULT_IOU
    default_sz   = model_info.get("inference_image_size", config.DEFAULT_IMGSZ) if model_info else config.DEFAULT_IMGSZ
    conf_thresh = st.slider("Confidence threshold", 0.10, 0.95, float(default_conf), 0.05)
    iou_thresh  = st.slider("IoU / NMS threshold",  0.10, 0.95, float(default_iou),  0.05)
    img_size    = st.select_slider("Inference image size", [320, 480, 640, 800, 960], value=int(default_sz))
    save_to_db  = st.checkbox("💾 Save results to database", value=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
hero_banner("Live Detection Center", "Upload road images or videos for AI-powered pothole detection", "🔍",
            badge="YOLO11n · Real Inference · Results Saved to DB")

if model_error:
    info_box(f"❌ Model not available: {model_error}<br>Ensure <code>models/best.pt</code> exists.", kind="critical")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_img, tab_vid, tab_demo = st.tabs(["🖼️ Image Detection", "🎬 Video Detection", "▶ Demo Samples"])

# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab_img:
    section_header("Image Upload & Detection")
    uploaded = st.file_uploader(
        "Upload a road image (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        key="ld_img_upload",
    )

    if uploaded:
        filename = uploaded.name
        if not is_accepted_image(filename):
            st.error(f"Unsupported file type: {Path(filename).suffix}")
        else:
            try:
                pil_img = Image.open(uploaded)
                validate_image(pil_img)
            except Exception as exc:
                st.error(f"Cannot read image: {exc}")
                st.stop()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📷 Original Image**")
                st.image(pil_img, use_container_width=True)

            with st.spinner("⚡ Running YOLO11n inference…"):
                try:
                    t0 = time.perf_counter()
                    annotated, detections = run_image_inference(
                        model, pil_img,
                        conf=conf_thresh, iou=iou_thresh,
                        imgsz=img_size, source_name=filename,
                    )
                    elapsed = time.perf_counter() - t0
                except RuntimeError as exc:
                    st.error(f"Inference error: {exc}")
                    st.stop()

            with col2:
                st.markdown("**🎯 Detection Result**")
                st.image(annotated, use_container_width=True)

            # Enrich with severity
            w, h = pil_img.size
            detections = classify_detections(detections, image_width=w, image_height=h)

            # Metrics
            n_det = len(detections)
            fps_val = round(1.0 / elapsed, 1) if elapsed > 0 else 0
            metric_row([
                {"val": n_det,            "lbl": "Detections"},
                {"val": f"{elapsed:.2f}s","lbl": "Inference Time"},
                {"val": f"{fps_val}",     "lbl": "FPS"},
                {"val": f"{w}×{h}",       "lbl": "Image Size"},
                {"val": conf_thresh,      "lbl": "Conf Threshold"},
            ])

            if n_det == 0:
                info_box("No potholes detected at this confidence threshold. Try lowering the slider.")
            else:
                section_header(f"Detection Results — {n_det} pothole(s)")
                import plotly.express as px
                df = pd.DataFrame(detections)
                display_cols = ["detection_index", "class_name", "confidence", "severity", "area_ratio", "x1", "y1", "x2", "y2"]
                avail_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[avail_cols], use_container_width=True, hide_index=True)

                # Confidence histogram
                fig_conf = px.histogram(
                    df, x="confidence", nbins=10,
                    title="Confidence Score Distribution",
                    color_discrete_sequence=["#6366f1"],
                    template="plotly_dark",
                )
                fig_conf.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#c4c4e0", margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig_conf, use_container_width=True)

                # Save to DB
                if save_to_db:
                    try:
                        records = []
                        for d in detections:
                            records.append({
                                "source_name": filename,
                                "source_type": "image",
                                "detection_index": d.get("detection_index", 0),
                                "class_id": d.get("class_id", 0),
                                "class_name": d.get("class_name", "pothole"),
                                "confidence": d["confidence"],
                                "x1": d["x1"], "y1": d["y1"],
                                "x2": d["x2"], "y2": d["y2"],
                                "image_width": w, "image_height": h,
                                "conf_threshold": conf_thresh,
                                "iou_threshold": iou_thresh,
                                "imgsz": img_size,
                                "severity": d.get("severity"),
                                "area_ratio": d.get("area_ratio"),
                            })
                        saved_ids = save_detections_batch(records)
                        st.success(f"✅ {len(saved_ids)} detection(s) saved to database.")

                        # Optional location entry
                        with st.expander("📍 Add location for this detection"):
                            lc1, lc2 = st.columns(2)
                            with lc1:
                                lat = st.number_input("Latitude", -90.0, 90.0, 0.0, format="%.6f", key="img_lat")
                            with lc2:
                                lon = st.number_input("Longitude", -180.0, 180.0, 0.0, format="%.6f", key="img_lon")
                            area = st.text_input("Area name (optional)", key="img_area")
                            addr = st.text_input("Address (optional)", key="img_addr")
                            notes = st.text_input("Notes (optional)", key="img_notes")
                            if st.button("📍 Save Location", key="img_save_loc"):
                                if lat == 0.0 and lon == 0.0:
                                    st.warning("Enter non-zero coordinates to save a location.")
                                else:
                                    save_location(
                                        lat=lat, lon=lon,
                                        detection_id=saved_ids[0] if saved_ids else None,
                                        address=addr or None,
                                        location_source="manual",
                                        area_name=area or None,
                                        notes=notes or None,
                                    )
                                    st.success("📍 Location saved!")
                    except Exception as db_e:
                        st.warning(f"Could not save to DB: {db_e}")

            # Downloads
            section_header("Downloads")
            stem = safe_filename(Path(filename).stem)
            dc1, dc2, dc3 = st.columns(3)

            img_buf = io.BytesIO()
            annotated.save(img_buf, format="PNG")
            img_buf.seek(0)
            with dc1:
                st.download_button("⬇️ Annotated Image (PNG)", data=img_buf,
                                   file_name=f"{stem}_annotated.png", mime="image/png")
            csv_b = detections_to_csv_bytes(detections, IMAGE_DETECTION_COLUMNS + ["severity", "area_ratio"])
            with dc2:
                st.download_button("⬇️ Detections CSV", data=csv_b,
                                   file_name=f"{stem}_detections.csv", mime="text/csv")
            json_b = build_json_summary(
                source_filename=filename, conf=conf_thresh, iou=iou_thresh,
                imgsz=img_size, detection_count=n_det,
                extra={"inference_time_s": round(elapsed, 3)},
            )
            with dc3:
                st.download_button("⬇️ JSON Summary", data=json_b,
                                   file_name=f"{stem}_summary.json", mime="application/json")

    else:
        info_box("Upload a road image (JPG, PNG, WEBP) to begin detection.")


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
with tab_vid:
    section_header("Video Upload & Detection")
    info_box(
        "⚠️ Video processing is CPU-bound. Use the frame limit to keep demo time short.<br>"
        "No live camera simulation — only uploaded video files are processed.",
        kind="warn",
    )

    max_frames = st.slider("Max frames to process", 10, config.MAX_VIDEO_FRAMES,
                           config.DEFAULT_VIDEO_FRAMES, 10)
    uploaded_vid = st.file_uploader("Upload a road video (MP4, AVI, MOV)",
                                    type=["mp4", "avi", "mov"], key="ld_vid_upload")

    if uploaded_vid:
        vname = uploaded_vid.name
        if not is_accepted_video(vname):
            st.error(f"Unsupported video format: {Path(vname).suffix}")
        else:
            st.video(uploaded_vid)
            video_bytes = uploaded_vid.read()

            if st.button("🚀 Process Video", key="ld_process_vid"):
                prog = st.progress(0)
                stat = st.empty()

                def _on_progress(cur, total):
                    pct = int(cur / max(total, 1) * 100)
                    prog.progress(min(pct, 100))
                    stat.text(f"Processing frame {cur} / {total}…")

                with st.spinner("Running frame-by-frame inference…"):
                    try:
                        out_path, vid_dets, vid_sum = process_video(
                            model, video_bytes=video_bytes, video_filename=vname,
                            conf=conf_thresh, iou=iou_thresh, imgsz=img_size,
                            max_frames=max_frames, progress_callback=_on_progress,
                        )
                    except Exception as exc:
                        st.error(f"Video processing failed: {exc}")
                        st.stop()

                prog.progress(100)
                stat.text("✅ Processing complete")

                metric_row([
                    {"val": vid_sum.get("frames_processed", 0), "lbl": "Frames Processed"},
                    {"val": vid_sum.get("total_detections", 0), "lbl": "Total Detections"},
                    {"val": f"{vid_sum.get('processing_time_s', 0):.1f}s", "lbl": "Processing Time"},
                    {"val": vid_sum.get("video_fps") or "N/A", "lbl": "Source FPS"},
                ])

                if out_path:
                    with open(out_path, "rb") as vf:
                        vdata = vf.read()
                    vstem = safe_filename(Path(vname).stem)
                    st.download_button("⬇️ Download Annotated Video (MP4)", data=vdata,
                                       file_name=f"{vstem}_annotated.mp4", mime="video/mp4")

                if vid_dets:
                    import plotly.express as px
                    df_vid = pd.DataFrame(vid_dets)
                    fig_v = px.bar(
                        df_vid.groupby("frame_index").size().reset_index(name="count"),
                        x="frame_index", y="count",
                        title="Detections per Frame",
                        color_discrete_sequence=["#8b5cf6"],
                        template="plotly_dark",
                    )
                    fig_v.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c4c4e0",
                    )
                    st.plotly_chart(fig_v, use_container_width=True)

                    st.markdown("#### Per-detection table (first 200 rows)")
                    st.dataframe(df_vid[VIDEO_DETECTION_COLUMNS].head(200), use_container_width=True)

                    if save_to_db:
                        try:
                            records = [
                                {
                                    "source_name": vname, "source_type": "video",
                                    "detection_index": i,
                                    "class_id": d.get("class_id", 0),
                                    "class_name":d.get("class_name", "pothole"),
                                    "confidence": d["confidence"],
                                    "x1": d["x1"], "y1": d["y1"],
                                    "x2": d["x2"], "y2": d["y2"],
                                    "frame_index": d.get("frame_index"),
                                    "timestamp_s": d.get("timestamp_s"),
                                    "conf_threshold": conf_thresh,
                                    "iou_threshold": iou_thresh,
                                    "imgsz": img_size,
                                }
                                for i, d in enumerate(vid_dets)
                            ]
                            saved = save_detections_batch(records)
                            st.success(f"✅ {len(saved)} video detections saved to database.")
                        except Exception as db_e:
                            st.warning(f"Could not save to DB: {db_e}")

                    vc1, vc2 = st.columns(2)
                    csv_v = detections_to_csv_bytes(vid_dets, VIDEO_DETECTION_COLUMNS)
                    with vc1:
                        st.download_button("⬇️ Detections CSV", data=csv_v,
                                           file_name=f"{safe_filename(Path(vname).stem)}_detections.csv",
                                           mime="text/csv")
                    jv = build_json_summary(
                        source_filename=vname, conf=conf_thresh, iou=iou_thresh,
                        imgsz=img_size, detection_count=len(vid_dets),
                        frames_processed=vid_sum.get("frames_processed"),
                        extra={"processing_time_s": vid_sum.get("processing_time_s")},
                    )
                    with vc2:
                        st.download_button("⬇️ JSON Summary", data=jv,
                                           file_name=f"{safe_filename(Path(vname).stem)}_summary.json",
                                           mime="application/json")
                else:
                    info_box("No potholes detected. Try lowering the confidence threshold.")

    else:
        info_box("Upload a road video (MP4, AVI, MOV) to run frame-by-frame detection.")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO SAMPLES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_demo:
    section_header("Run Demo on Sample Images")
    sample_dir = config.SAMPLE_IMAGES_DIR
    samples = sorted(sample_dir.glob("*.png")) + sorted(sample_dir.glob("*.jpg")) if sample_dir.is_dir() else []

    if not samples:
        empty_state("No Sample Images Found", f"Place sample images in {sample_dir}", "🖼️")
    else:
        demo_choice = st.selectbox("Select sample image", [p.name for p in samples[:8]], key="demo_sel")
        if st.button("▶ Run Demo Inference", key="run_demo_btn"):
            chosen = sample_dir / demo_choice
            pil_demo = Image.open(chosen)
            with st.spinner("Running demo inference…"):
                try:
                    t0d = time.perf_counter()
                    ann_demo, det_demo = run_image_inference(
                        model, pil_demo,
                        conf=conf_thresh, iou=iou_thresh,
                        imgsz=img_size, source_name=demo_choice,
                    )
                    elapsed_d = time.perf_counter() - t0d
                except RuntimeError as exc:
                    st.error(f"Demo inference failed: {exc}")
                    st.stop()

            det_demo = classify_detections(det_demo,
                                           image_width=pil_demo.size[0],
                                           image_height=pil_demo.size[1])
            d1, d2 = st.columns(2)
            with d1:
                st.image(pil_demo, caption="Original", use_container_width=True)
            with d2:
                st.image(ann_demo, caption=f"Detected: {len(det_demo)} pothole(s)", use_container_width=True)

            metric_row([
                {"val": len(det_demo),        "lbl": "Detections"},
                {"val": f"{elapsed_d:.2f}s",  "lbl": "Inference Time"},
                {"val": f"{round(1/elapsed_d,1) if elapsed_d>0 else 0}", "lbl": "FPS"},
            ])

            if det_demo:
                df_demo = pd.DataFrame(det_demo)
                disp = [c for c in ["class_name", "confidence", "severity", "x1", "y1", "x2", "y2"] if c in df_demo.columns]
                st.dataframe(df_demo[disp], use_container_width=True, hide_index=True)
                if save_to_db:
                    try:
                        recs = [{
                            "source_name": demo_choice, "source_type": "demo",
                            "detection_index": i,
                            "class_id": d.get("class_id", 0),
                            "class_name": d.get("class_name", "pothole"),
                            "confidence": d["confidence"],
                            "x1": d["x1"], "y1": d["y1"],
                            "x2": d["x2"], "y2": d["y2"],
                            "image_width": pil_demo.size[0],
                            "image_height": pil_demo.size[1],
                            "conf_threshold": conf_thresh,
                            "iou_threshold": iou_thresh,
                            "imgsz": img_size,
                            "severity": d.get("severity"),
                            "area_ratio": d.get("area_ratio"),
                        } for i, d in enumerate(det_demo)]
                        save_detections_batch(recs)
                        st.success(f"✅ {len(recs)} demo detection(s) saved.")
                    except Exception as db_e:
                        st.warning(f"DB save failed: {db_e}")
            else:
                info_box("No potholes detected in this sample at the current threshold.")
