# Project Report: AI-Based Road Pothole Detection System

---

## 1. Abstract

Road surface defects, particularly potholes, pose significant risks to vehicle safety
and impose economic costs through vehicle damage and road maintenance expenditure.
Manual road inspection is expensive and spatially limited.  This project investigates
automated pothole detection using YOLO-family convolutional neural networks trained on
a custom annotated dataset.  We compare YOLOv8n, YOLO11n (640 px), and YOLO11n (800 px)
against a DETR-R50 transformer baseline, achieving a best test-set mAP@50 of 78.05%
with YOLO11n.  A Streamlit application provides a locally-deployable demonstration of
the trained model.

---

## 2. Problem Statement

Potholes form when water infiltrates road surface cracks, freezes, expands, and
weakens the sub-surface material.  Manual inspection cannot keep pace with the scale
of road networks.  Computer vision offers a scalable alternative: cameras mounted on
survey vehicles or smartphones can capture road images that a trained detector analyses
automatically.

---

## 3. Objectives

1. Collect and annotate a dataset of road pothole images.
2. Train YOLO-family detectors and compare their performance.
3. Compare with a transformer-based baseline (DETR-R50).
4. Deploy the best checkpoint in a demonstrable web application.
5. Document limitations and define a roadmap for future improvements.

---

## 4. Dataset and Annotations

| Property | Value |
|---|---|
| Total images | 665 |
| Train / Val / Test | 532 / 66 / 67 |
| Annotation format | Pascal VOC XML bounding boxes |
| Conversion | XML → YOLO `.txt` format |
| Class | `pothole` (class ID 0) |
| Test instances | 161 ground-truth boxes across 67 test images |

Images were sourced from publicly available pothole datasets and supplemented with
manually collected road photographs.  Annotations were verified and corrected before
training.

---

## 5. Data Preprocessing

- Images resized to the training image size (640 or 800 px) by Ultralytics YOLO
  during training.
- Standard Ultralytics augmentations applied: mosaic, random flip, colour jitter,
  random scale.
- Pascal VOC XML annotations converted to YOLO `.txt` format using a custom
  conversion script run in Google Colab.

---

## 6. Model Architecture

### YOLO11n (primary deployment model)

YOLO11n is the nano version of the YOLO11 architecture from Ultralytics.
It uses a CSP (Cross Stage Partial) backbone, a PANet neck, and a decoupled
detection head.  At the nano scale it prioritises speed over maximum accuracy,
making it suitable for real-time edge deployment.

### YOLOv8n (comparison baseline)

YOLOv8n is the preceding generation nano model.  It shares a similar design pattern
but uses an older backbone variant.

### DETR-R50 (architecture baseline)

DETR (Detection Transformer) uses a ResNet-50 backbone with transformer encoder-
decoder layers and bipartite matching loss.  It does not use NMS and is generally
slower but architecturally different.

---

## 7. Training Methodology

All YOLO models were trained on Google Colab using the Ultralytics Python API.

| Experiment | Architecture | Image size | Epochs | Best epoch |
|---|---|---|---|---|
| A1 — YOLOv8n | YOLOv8n | 640 | 43 | 33 |
| A2 — YOLO11n-640 | YOLO11n | 640 | 46 | 36 |
| A4 — YOLO11n-800 | YOLO11n | 800 | 50 | 49 |
| A (DETR) | DETR-R50 | Default | — | — |

- Pretrained COCO weights used as starting point for all YOLO models.
- Early stopping was not used; best checkpoint selected by validation mAP@50-95.
- Learning rate and batch size used Ultralytics defaults unless otherwise noted.
- No custom augmentation beyond Ultralytics defaults.

---

## 8. Evaluation Methodology

**Matching rule:** IoU ≥ 0.50 between predicted and ground-truth box = true positive.

**Metrics:**
- **Precision:** TP / (TP + FP)
- **Recall:** TP / (TP + FN)
- **F1:** 2 × Precision × Recall / (Precision + Recall)
- **mAP@50:** mean Average Precision at IoU 0.50
- **mAP@50-95:** mean AP averaged over IoU 0.50 to 0.95 in steps of 0.05

**Splits:**
- Validation metrics were recorded continuously during training.
- Test-set evaluation used the held-out 67-image split not seen during training.

---

## 9. Verified Results

### Test-split comparison (source: `final_model_comparison.csv`)

| Model | Prec. | Recall | mAP@50 | mAP@50-95 | F1 | Inf. (ms) |
|---|---|---|---|---|---|---|
| YOLOv8n | 79.88% | 66.60% | 76.84% | 48.44% | 72.64 | 11.6 |
| **YOLO11n** | **84.96%** | **66.67%** | **78.05%** | **49.31%** | **74.71** | 12.2 |
| DETR-R50  | 48.46% | 78.26% | 68.50% | 40.60% | 59.86 | — |

> **Note:** These test-set figures are for the 640 px YOLO11n checkpoint.
> The deployed `best.pt` was trained at 800 px and was not re-evaluated on the
> test set at the time of submission.

### Best validation metrics per checkpoint (source: `phase63_training_audit.csv`)

| Checkpoint | Best val mAP@50 | Best val mAP@50-95 | Best epoch |
|---|---|---|---|
| YOLOv8n_640 | 81.86% | 53.61% | 33 |
| YOLO11n_640 | 82.37% | 54.60% | 36 |
| **YOLO11n_800** | **86.97%** | **58.67%** | **49** |
| YOLO11n_960 | 81.72% | 53.30% | 49 |

> ⚠️ Validation metrics are not independent.  They were used to select the best
> checkpoint and cannot substitute for test-set evaluation.

---

## 10. Application Architecture

```
Streamlit (app.py)
    │
    ├── config.py           ← project-level constants
    ├── src/model_loader.py ← @st.cache_resource YOLO loading
    ├── src/image_inference.py ← PIL → YOLO.predict → PIL + records
    ├── src/video_inference.py ← OpenCV frame loop + annotated writer
    ├── src/reporting.py    ← CSV/JSON serialisation
    └── src/validation.py   ← extension and record checks
```

---

## 11. Implementation

The application was built with:

- **Streamlit** — browser UI with tab navigation, sliders, file uploaders
- **Ultralytics YOLO** — model inference via `model.predict()`
- **OpenCV** — video frame decoding and re-encoding
- **Pillow** — image I/O and format conversion
- **Pandas** — detection table display and CSV export
- **Plotly** — confidence histogram and per-frame bar chart

---

## 12. Limitations

- The dataset is small (665 images); generalisation to unseen road types is uncertain.
- Only one class is detected; cracks, speed bumps, and manholes are ignored.
- Physical pothole depth cannot be determined from monocular RGB images.
- The Streamlit app is CPU-bound; inference at imgsz=800 on CPU is slow (seconds
  per image; minutes per video clip).
- GPS location is not captured.
- No trained segmentation model exists despite the manual annotation pilot.
- YOLO11n-800 test-set metrics are not available from current artifacts.

---

## 13. Future Scope

- Larger, geographically diverse dataset
- Instance segmentation (YOLO11n-Seg or Mask R-CNN)
- GPS metadata capture and road map integration
- Mobile-optimised model (TFLite or ONNX export)
- Severity proxy from bounding-box area ratio
- Continuous active learning from new road footage

---

## 14. Conclusion

This project demonstrates that lightweight YOLO models can be trained on a modest
custom dataset to detect road potholes with useful accuracy (mAP@50 ≈ 78 – 87%).
YOLO11n at 800 px achieved the best validation performance and is deployed in the
accompanying Streamlit application.  The project is a working prototype, not a
production system, and its limitations are clearly documented.
