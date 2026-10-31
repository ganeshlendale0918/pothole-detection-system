# RoadSight Intelligence Platform v2.0 — Upgrade Audit

## Audit Date
2026-10-30 (UTC)

## 1. Project Entry Point

| File | Role |
|------|------|
| `app.py` | Main Streamlit entry point, model loading, sidebar navigation, landing page KPIs |
| `config.py` | Centralised configuration — paths, thresholds, defaults |
| `data.yaml` | YOLOv8/YOLO11 dataset YAML (for reference only) |
| `requirements.txt` | Python dependency list |

**Run command:** `streamlit run app.py`

---

## 2. Existing Pages (Pre-Upgrade)

The existing project entered this upgrade with 7 pages already built:

| Page | File | Status |
|------|------|--------|
| Landing / Home | `app.py` | ✅ Functional |
| Executive Overview | `pages/1_Executive_Overview.py` | ✅ Functional |
| Live Detection | `pages/2_Live_Detection.py` | ✅ Functional |
| Detection History | `pages/3_Detection_History.py` | ✅ Functional |
| GIS Map | `pages/4_GIS_Map.py` | ✅ Functional |
| Road Condition Intelligence | `pages/5_Road_Condition_Intelligence.py` | ✅ Functional |
| Repair Management | `pages/6_Repair_Management.py` | ✅ Functional |
| Advanced Analytics | `pages/7_Advanced_Analytics.py` | ✅ Functional |

**Missing (created during this upgrade):**

| Page | File | Status |
|------|------|--------|
| Simulation Lab | `pages/8_Simulation_Lab.py` | ✅ Created |
| Model Performance | `pages/9_Model_Performance.py` | ✅ Created |
| Reports & Export | `pages/10_Reports_Export.py` | ✅ Created |
| Settings | `pages/11_Settings.py` | ✅ Created |

---

## 3. Model & Weights

| Item | Path | Status |
|------|------|--------|
| Primary Checkpoint | `models/best.pt` | ✅ Present (5.25 MB) |
| Baseline Comparison | `models/yolo11n_640.pt` | ✅ Present |
| Baseline Comparison | `models/yolov8n_640.pt` | ✅ Present |
| Model Metadata | `models/model_metadata.json` | ✅ Present |

**Architecture:** YOLO11n (Nano) — Ultralytics  
**Training:** Custom-trained on 665 annotated road images  
**Default Inference Size:** 800 × 800 px  
**Default Conf Threshold:** 0.45  
**Default IoU Threshold:** 0.45  

> **IMPORTANT:** Model weights were never modified, retrained, or replaced during this upgrade.

---

## 4. Inference Pipeline

| Module | File | Function |
|--------|------|----------|
| Model loader | `src/model_loader.py` | `get_model()`, `get_model_info()`, `load_model_metadata()` |
| Image inference | `src/image_inference.py` | Frame-level YOLO predict + bounding box extraction |
| Video inference | `src/video_inference.py` | Frame-by-frame extraction, batched inference |
| Severity classification | `src/severity.py` | Area-ratio based severity assignment |
| Validation | `src/validation.py` | Model path validation |

**Caching:** Model loaded once with `@st.cache_resource` in `app.py` and shared via `st.session_state`.

---

## 5. Database & Storage

| Table | Purpose |
|-------|---------|
| `detections` | Each saved detection bounding box with confidence, severity |
| `locations` | Optional GPS/user-entered coordinates linked to detections |
| `repair_tasks` | Repair lifecycle records |
| `repair_status_log` | Immutable audit trail for status transitions |
| `simulation_runs` | Isolated simulation scenario metadata |
| `simulation_records` | Simulated pothole records (never in real dashboards) |
| `app_settings` | Persistent key-value platform settings |

**Database:** SQLite at `data/roadintel.db` with WAL mode and foreign keys enabled.  
**Persistence:** Yes — all records survive restarts.  
**Simulation Isolation:** `simulation_runs` and `simulation_records` tables are strictly separate.

---

## 6. Research Reports

Located in `research_reports/results/`:

| File | Contents |
|------|----------|
| `final_model_comparison.csv` | YOLO11n vs YOLOv8n vs DETR-R50 on test set |
| `final_model_comparison.json` | Same data + ranking in JSON |
| `experiment_results.csv` | Per-experiment evaluation history |
| `phase63_training_audit.csv` | Training phase audit log |
| Multiple phase subdirectories | NMS analysis, confidence sweeps, error analysis |

---

## 7. Dataset

| Split | Count |
|-------|-------|
| Total | 665 images |
| Training | 532 |
| Validation | 66 |
| Test | 67 |
| Classes | 1 (pothole) |
| Annotation Format | Pascal VOC XML → YOLO |

---

## 8. Model Evaluation Results (From Files — Not Fabricated)

| Model | Precision | Recall | F1 | mAP@50 | mAP@50-95 | Inf (ms) |
|-------|-----------|--------|----|--------|-----------|----------|
| **YOLO11n** *(selected)* | 84.96% | 66.67% | 74.71% | 78.05% | 49.31% | 12.2 |
| YOLOv8n | 79.88% | 66.60% | 72.64% | 76.84% | 48.44% | 11.6 |
| DETR-R50 | 48.46% | 78.26% | 59.86% | 68.50% | 40.60% | N/A |

---

## 9. Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit>=1.35` | App framework |
| `ultralytics>=8.3` | YOLO11n inference |
| `opencv-python-headless>=4.9` | Image/video processing |
| `Pillow>=10.0` | Image handling |
| `pandas>=2.0` | Data manipulation |
| `numpy>=1.24` | Numerical ops |
| `plotly>=5.18` | Interactive charts |
| `folium>=0.16` | Map rendering |
| `streamlit-folium>=0.20` | Folium ↔ Streamlit bridge |
| `openpyxl>=3.1` | Excel export |
| `fpdf2>=2.7` | PDF generation |
| `geopy>=2.4` | Address geocoding |
| `pytest>=8.0` | Testing |

---

## 10. Current Limitations

| Limitation | Notes |
|-----------|-------|
| Webcam support | Depends on browser/OS permissions and Streamlit compatibility |
| Real-time streaming | Not available — app processes uploaded files only |
| PDF report generation | Basic text PDF via fpdf2; no chart embedding |
| Geocoding | Requires internet; Nominatim rate limits apply |
| Video processing | Capped at 500 frames for memory safety |
| Multi-user concurrency | SQLite WAL mode supports limited concurrent writes |

---

## 11. Upgrade Summary

All 11 navigation pages are now implemented. The upgrade preserved every existing feature and added:
- Pages 8–11 (Simulation Lab, Model Performance, Reports & Export, Settings)
- Full documentation suite in `docs/`
- No model weights modified, no existing records broken
