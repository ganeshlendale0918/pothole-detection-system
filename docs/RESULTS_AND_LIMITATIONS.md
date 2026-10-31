# Results and Limitations

## Verified Results

All metrics below are sourced from experiment report files included in the
submission assets.  No values have been fabricated or estimated.

### Test-split evaluation (67 images, 161 instances)

Source: `research_reports/results/final_model_comparison.csv`
Matching IoU threshold: 0.50

| Model | Precision | Recall | F1 | mAP@50 | mAP@50-95 | Inference (ms) |
|---|---|---|---|---|---|---|
| YOLOv8n (640 px) | 79.88% | 66.60% | 72.64 | 76.84% | 48.44% | 11.6 |
| YOLO11n (640 px) | 84.96% | 66.67% | 74.71 | 78.05% | 49.31% | 12.2 |
| DETR-R50 | 48.46% | 78.26% | 59.86 | 68.50% | 40.60% | — |

**YOLO11n ranked first** on mAP@50 and F1 among the three compared architectures.
DETR-R50 achieved higher recall but substantially lower precision.

### Validation-split metrics from training (best checkpoint per model)

Source: `research_reports/results/phase63_training_audit.csv`

| Checkpoint | Best val mAP@50 | Best val mAP@50-95 | Epoch |
|---|---|---|---|
| YOLOv8n_640 | 81.86% | 53.61% | 33 / 43 |
| YOLO11n_640 | 82.37% | 54.60% | 36 / 46 |
| **YOLO11n_800** | **86.97%** | **58.67%** | **49 / 50** |
| YOLO11n_960 | 81.72% | 53.30% | 49 / 50 |

The YOLO11n_800 checkpoint (`models/best.pt`) is the deployed model.
It achieved the highest validation mAP across all experiments.

> ⚠️ Validation metrics were used for checkpoint selection.
> They do not constitute independent test-set performance.

---

## Metrics Not Available from Current Artifacts

| Metric | Status |
|---|---|
| YOLO11n-800 test-set precision / recall / mAP | **Not verified** |
| Per-class AP (single class: pothole) | Not separately reported |
| CPU inference latency at imgsz=800 | Not measured |
| False-positive / false-negative count | Not verified |
| Memory usage | Not measured |

---

## Limitations

### Dataset limitations

- 665 images is a relatively small dataset for a generalised road defect detector.
- Images were not collected from a geographically diverse set of road surfaces.
- Image quality varies (resolution, lighting, camera angle).
- Only potholes are labelled; other defects are present but not annotated.

### Model limitations

- The model has been trained for only one class (`pothole`).
- Small potholes may be missed at lower image resolutions.
- Heavily occluded or partially visible potholes may be under-detected.
- The model may produce false positives on shadows, manhole covers, or road markings
  that visually resemble potholes.

### Application limitations

- Physical pothole depth, volume, and danger level **cannot** be estimated from
  a single monocular RGB image.
- The app does not capture GPS coordinates; location information is not available
  unless the user provides it.
- Severity indicators (if shown) are proxy estimates based on bounding-box area
  relative to image area and should not be treated as ground-truth measurements.
- CPU inference is slow; processing a full video at imgsz=800 may take several
  minutes on a laptop.
- No trained segmentation model exists.  The segmentation pilot section shows
  manually annotated masks only.

### Evaluation limitations

- Test-set evaluation was performed at 640 px image size.  The deployed checkpoint
  (800 px) was not re-evaluated on the test split at the time of submission.
- Validation metrics cannot be compared directly with test metrics because the
  validation set may have influenced model selection.
- mAP figures depend on the detection confidence threshold used during evaluation.
  If the threshold was different from the default (0.45), results are not directly
  comparable.

---

## Future Scope

1. **Larger dataset** — collect 5,000+ images with diverse geography and weather.
2. **Instance segmentation** — train YOLO11n-Seg or Mask R-CNN for pixel-level masks.
3. **GPS integration** — attach EXIF GPS metadata for road-level heatmaps.
4. **Severity heuristic** — bounding-box area ratio as an experimental proxy metric.
5. **Edge deployment** — TFLite / ONNX / CoreML export for mobile survey vehicles.
6. **Active learning** — retrain from new field images flagged by the deployed app.
7. **Multi-class extension** — add crack, rutting, ravelling, edge break categories.
