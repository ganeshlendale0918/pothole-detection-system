# FACTS.md — read-only extraction (no recomputation)

Extracted 2026-10-31 from files and command output under `pothole-detection-system/`.
Line counts: PowerShell `Get-Content | Measure-Object -Line` (counts **non-blank** lines). Excluded: `.venv`, `__pycache__`, `.pytest_cache`.
Nothing below is invented. `[TO CONFIRM]` = not found in project files.

---

## 1. PROJECT

- **Folder / app names:** `pothole-detection-system`; Streamlit title `RoadSight Intelligence Platform` (`config.py` `APP_TITLE`); README heading `AI-Based Road Pothole Detection System`; `model_metadata.json` `"project": "AI-Based Road Pothole Detection"`; `PROJECT_VERSION` `2.0.0` (`config.py`).
- **Purpose (README.md):** college academic project that trains and deploys a single-class (`pothole`) YOLO11n detector on 665 annotated road images; Streamlit app loads the checkpoint locally for image/video detection, research metrics, and documented limitations.
- **Purpose (app.py landing):** “AI-powered pothole detection, geospatial analytics, and repair lifecycle management”; landing KPIs from SQLite (`get_kpi_summary`).
- **Users:** not named as municipal corporations or similar in README/app.py. README: academic project. App is a local Streamlit tool for detection, mapping, repair tracking, analytics. **Named target users: [TO CONFIRM].**
- **Student name / roll / guide / academic year / HOD:** not present in repo. **[TO CONFIRM] — only the student knows these.** HOD Prof. A. M. Bainwad: not in any project file.
- **Project logo / title-page image:** no dedicated logo asset found under project `assets/` besides sample images referenced in README. App uses emoji `🛣️` as `page_icon` (`app.py`). Whether the department report needs a logo: **[TO CONFIRM].**
- **Commercial chapter:** no selling price, municipal contract figures, or market cost model in docs. App default repair-cost constants only (`config.py`): Low 500, Medium 1500, High 4000, Critical 10000 (units not stated). **Price idea / commercial costs: [TO CONFIRM] — write as labelled assumptions if used.**

---

## 2. MODEL — which checkpoint `models/best.pt` is

From `models/model_metadata.json` (full contents):

```json
{
  "project": "AI-Based Road Pothole Detection",
  "main_model": "YOLO11n custom-trained checkpoint",
  "checkpoint_source": "/content/drive/MyDrive/Colab_project_working/pothhole_project/experiments/A4_yolo11n_img800/weights/best.pt",
  "inference_image_size": 800,
  "class_names": ["pothole"],
  "default_confidence": 0.45,
  "default_iou": 0.45,
  "created_utc": "2026-10-13T17:13:38.858006+00:00",
  "sample_images_copied": 8,
  "warning": "Confirm checkpoint metrics from the corresponding saved evaluation reports. Do not treat validation metrics as independent test-set performance."
}
```

- **Training experiment ID:** `A4_yolo11n_img800` (`model_metadata.json` `checkpoint_source`).
- **Architecture / YOLO version:** YOLO11n, Ultralytics (`README.md`, `app.py` spinner “Loading YOLO11n…”, `docs/RESULTS_AND_LIMITATIONS.md`).
- **Image size:** 800 px (`model_metadata.json` `inference_image_size`; `config.py` `DEFAULT_IMGSZ = 800`).
- **Training location:** Google Colab, pretrained on COCO (`README.md`, `docs/METHODOLOGY.md`).
- **File size:** `models/best.pt` 5,504,986 bytes (PowerShell `Get-ChildItem models`). `docs/TESTING.md` / `docs/UPGRADE_AUDIT.md` say 5.25 MB.
- **Parameters / GFLOPs:** not recorded in `model_metadata.json` or the result files listed in §3. **[TO CONFIRM / not in artifacts].**

### Which comparison rows belong to `best.pt`

- **Does belong:** `phase63_training_audit.csv` row `YOLO11n_800` (docs/RESULTS_AND_LIMITATIONS.md: “The YOLO11n_800 checkpoint (`models/best.pt`) is the deployed model.”).
- **Does belong:** `research_reports/results/final_test_comparison/final_test_metrics.json` and `fixed_threshold_model_comparison.json` rows labelled `YOLO11n_800` / Image_size 800 (same experiment family; files exist independently of `final_model_comparison.json`).
- **Does NOT belong to `best.pt`:** the `"Model": "YOLO11n"` row in `final_model_comparison.json` / `.csv`. Those numbers match `experiment_results.csv` row `A2_yolo11n` (640-class comparison: Precision 0.849615…, mAP50 0.780527…). `docs/RESULTS_AND_LIMITATIONS.md` labels that table “YOLO11n (640 px)”.
- **Does NOT belong:** `experiment_results.csv` `A1_yolov8n`.

### `yolo11n_640.pt` and `yolov8n_640.pt`

Present on disk (`models/`): `yolo11n_640.pt` 5,474,202 bytes; `yolov8n_640.pt` 6,249,834 bytes.
`docs/UPGRADE_PLAN.md` / `docs/UPGRADE_AUDIT.md`: “Baseline comparison model”.
`phase63_training_audit.csv`: `YOLO11n_640`, `YOLOv8n_640`.
`experiment_results.csv`: `A2_yolo11n`, `A1_yolov8n`.
App default path is only `models/best.pt` (`config.py`).

---

## 3. RESULTS (copied as stored; not recomputed)

### 3.1 `research_reports/results/final_model_comparison.json`

Columns on each model object: Model, Architecture, Test Images, Test Instances, Precision, Recall, mAP50, mAP50-95, Inference (ms). Ranking: Model, Overall Accuracy Score, Rank.

JSON as stored: three models YOLOv8n / YOLO11n / DETR-R50; ranking YOLO11n 70.74 rank 1, YOLOv8n 68.88 rank 2, DETR-R50 59.14 rank 3.

| Field recorded in this file? | |
|---|---|
| Split | not a column; `docs/RESULTS_AND_LIMITATIONS.md` says test-split, 67 images, 161 instances |
| Confidence | not in JSON |
| NMS IoU | not in JSON |
| Matching IoU | not in JSON; `docs/RESULTS_AND_LIMITATIONS.md` / `docs/METHODOLOGY.md` say matching IoU **0.50** for this table |

`docs/METHODOLOGY.md` inference defaults: confidence 0.45, IoU/NMS 0.45 — **not stored inside this JSON**.

**`best.pt` (A4 / 800 px) is not a row in this JSON.** The YOLO11n row is the 640 px test comparison (`A2_yolo11n`).

### 3.2 `research_reports/results/final_model_comparison.csv` (exact)

```
Model,Architecture,Test Images,Test Instances,Precision,Recall,mAP50,mAP50-95,Inference (ms),F1
YOLOv8n,CNN-based YOLO,67,161,79.88,66.6,76.84,48.44,11.6,72.64
YOLO11n,CNN-based YOLO,67,161,84.96,66.67,78.05,49.31,12.2,74.71
DETR-R50,CNN + Transformer,67,161,48.46,78.26,68.5,40.6,,59.86
```

(Precision/Recall/mAP here are percentages, unlike the JSON fractions.)

### 3.3 `research_reports/results/experiment_results.csv` (exact)

```
experiment,model,task,test_images,test_instances,precision,recall,mAP50,mAP50_95,inference_ms
A1_yolov8n,YOLOv8n,Object Detection,67,161,0.7988458542635455,0.6660044866868041,0.7684021827571268,0.484403976874331,11.6
A2_yolo11n,YOLO11n,Object Detection,67,161,0.8496145610855073,0.6667316791403359,0.7805271461143359,0.4930828637780472,12.2
```

No conf / NMS / matching IoU columns. No `A4_yolo11n_img800` row. Split implied by column names `test_images` / `test_instances`.

### 3.4 `research_reports/results/phase63_training_audit.csv` (exact)

```
model,training_log_exists,best_checkpoint_exists,last_checkpoint_exists,logged_epochs,best_epoch_by_mAP50_95,best_val_mAP50,best_val_mAP50_95
YOLOv8n_640,True,True,True,43,33,0.81856,0.53606
YOLO11n_640,True,True,True,46,36,0.82366,0.54597
YOLO11n_800,True,True,True,50,49,0.86971,0.58671
YOLO11n_960,True,False,False,50,49,0.81718,0.53297
```

Split: validation (column names `best_val_*`). Conf / NMS / matching IoU: not in this CSV.

**Row corresponding to `models/best.pt`:** `YOLO11n_800` — best_val_mAP50 **0.86971**, best_val_mAP50_95 **0.58671**, best epoch 49 / 50 logged epochs.

### 3.5 `research_reports/results/validation_ground_truth_size_analysis.csv`

Columns: `image,GT_objects,small,medium,large`. 66 data rows (image stems `potholes100` … `potholes98`). Full file as stored:

```
image,GT_objects,small,medium,large
potholes100,1,0,0,1
potholes108,13,11,1,1
potholes141,1,0,0,1
potholes15,1,0,0,1
potholes157,1,0,0,1
potholes159,1,0,0,1
potholes164,1,0,1,0
potholes182,1,0,1,0
potholes2,2,0,1,1
potholes203,3,0,0,3
potholes225,3,0,1,2
potholes23,1,0,0,1
potholes239,1,0,0,1
potholes243,1,0,0,1
potholes249,1,0,0,1
potholes256,1,0,0,1
potholes262,1,0,0,1
potholes291,1,0,0,1
potholes293,1,0,0,1
potholes294,18,15,3,0
potholes30,2,0,0,2
potholes309,4,0,2,2
potholes325,1,0,0,1
potholes33,2,0,1,1
potholes340,1,0,1,0
potholes342,1,0,0,1
potholes344,2,0,1,1
potholes345,4,2,1,1
potholes347,1,0,0,1
potholes389,2,0,1,1
potholes39,14,5,8,1
potholes398,1,0,0,1
potholes425,3,1,1,1
potholes44,1,0,0,1
potholes448,2,1,0,1
potholes45,5,1,2,2
potholes453,1,0,0,1
potholes463,5,3,1,1
potholes466,1,0,0,1
potholes468,8,1,1,6
potholes493,2,0,1,1
potholes5,1,0,0,1
potholes520,19,8,8,3
potholes524,1,0,0,1
potholes53,5,4,0,1
potholes553,1,0,0,1
potholes559,2,1,1,0
potholes56,3,1,2,0
potholes568,1,0,0,1
potholes586,2,0,0,2
potholes590,4,0,2,2
potholes595,1,0,0,1
potholes606,3,1,2,0
potholes611,3,0,2,1
potholes624,4,2,0,2
potholes633,2,0,1,1
potholes639,1,0,0,1
potholes65,1,0,0,1
potholes650,3,0,0,3
potholes70,1,0,0,1
potholes71,1,0,0,1
potholes72,2,1,1,0
potholes88,3,0,3,0
potholes93,1,0,0,1
potholes95,4,3,0,1
potholes98,1,0,0,1
```

No conf/NMS columns. Filename says validation; 66 rows matches `DATASET_VAL = 66`.

### 3.6 Extra files that **do** record TP/FP/FN for YOLO11n_800 (`best.pt` family)

These were **not** in the four named files above. Present on disk.

`research_reports/results/final_test_comparison/final_test_metrics.json`:

- YOLO11n_640, Image_size 640, Confidence 0.4, TP 107, FP 23, FN 54, Precision_% 82.31, Recall_% 66.46, F1_% 73.54
- **YOLO11n_800**, Image_size 800, Confidence 0.4, TP 113, FP 18, FN 48, Precision_% 86.26, Recall_% 70.19, F1_% 77.4

`research_reports/results/final_test_comparison/fixed_threshold_model_comparison.json` adds Test_images 67, Ground_truth 161, timings for YOLO11n_800: Preprocess_ms 6.1, Inference_ms 33.63, Postprocess_ms 3.68, Total_stage_ms 43.41, Approx_FPS 23.03. NMS IoU **not in that JSON**. Matching IoU **not in that JSON**.

**Doc conflict (do not hide):** `docs/RESULTS_AND_LIMITATIONS.md` table “Metrics Not Available” still says YOLO11n-800 test-set P/R/mAP **Not verified** and FP/FN **Not verified**. `docs/PROJECT_REPORT.md` §12: “YOLO11n-800 test-set metrics are not available from current artifacts.” Those sentences contradict the later `final_test_comparison/` files. Files on disk contain the numbers; older docs do not cite them.

### 3.7 Validation operating-point TP/FP/FN (not `best.pt` test set)

`research_reports/results/phase71_confidence_sweep/settings.json`: model path is A4 `best.pt`; **split validation**; image_count 66; imgsz 800; nms_iou 0.45; matching_iou 0.5; inference_confidence_floor 0.01.

`research_reports/results/phase70_error_investigation/operating_point_comparison.csv`:

```
confidence,nms_iou,images,GT_instances,TP,FP,FN,precision,recall,F1
0.25,0.45,66,187,161,50,26,0.7630331753554502,0.8609625668449198,0.8090452261306533
0.4,0.45,66,187,154,30,33,0.8369565217391305,0.8235294117647058,0.8301886792452831
```

These 66 images / 187 GT are **validation**, not the 67-image / 161-instance **test** split.

App inference defaults (`config.py`): DEFAULT_CONF 0.45, DEFAULT_IOU 0.45, DEFAULT_IMGSZ 800.

---

## 4. DATASET

| Fact | Value | Source |
|---|---|---|
| Total images | 665 | README.md, config.py, docs |
| Train | 532 | same |
| Val | 66 | same |
| Test | 67 | same |
| Test instances | 161 | experiment_results.csv, final_model_comparison, METHODOLOGY.md |
| Val instances | 187 | phase70 operating_point_comparison.csv (66 images) |
| Train instances | — | METHODOLOGY.md table shows em dash. **[TO CONFIRM]** |
| Classes | 1, `pothole` (id 0) | data.yaml, README, config.py |
| Annotation | Pascal VOC XML → YOLO txt | README, METHODOLOGY.md, config.py `DATASET_ANNOTATION_FORMAT` |
| YAML path (Colab) | `/content/drive/MyDrive/Colab_project_working/pothhole_project/dataset` | data.yaml |
| Splits in YAML | images/train, images/val, images/test | data.yaml |
| Source | “publicly available pothole datasets and supplemented with manually collected photographs” | METHODOLOGY.md, PROJECT_REPORT.md. **Named public dataset / URL: [TO CONFIRM]** |
| Licence | not in README, data.yaml, or docs | **[TO CONFIRM]** |

---

## 5. PAGES (11) — one sentence + `src/` modules

Home `app.py` is extra (landing + nav); not one of the 11.

1. **1_Executive_Overview.py** — KPI dashboard (detections, severity, repair status, timeline) from live SQLite. Uses `src.database`, `src.severity`, `src.ui_components`.
2. **2_Live_Detection.py** — Upload image/video, run YOLO11n, classify severity, save detections; optional manual lat/lon. Uses `src.model_loader`, `src.validation`, `src.image_inference`, `src.video_inference`, `src.reporting`, `src.severity`, `src.database`, `src.ui_components`.
3. **3_Detection_History.py** — Paginated filter/search/delete of saved detections. Uses `src.database`, `src.ui_components`, `src.severity`.
4. **4_GIS_Map.py** — Folium map of saved locations; add via manual coords, Nominatim geocode, or map click. Uses `src.database`, `src.severity`, `src.ui_components`.
5. **5_Road_Condition_Intelligence.py** — Area risk scores from real detections (formula on page). Uses `src.database`, `src.risk_score`, `src.ui_components`, `src.severity`.
6. **6_Repair_Management.py** — Repair task CRUD and status changes. Uses `src.database` (`VALID_STATUSES`, create/transition), `src.ui_components`.
7. **7_Advanced_Analytics.py** — Plotly charts from detection/repair records with date filters. Uses `src.database`, `src.ui_components`, `src.severity`.
8. **8_Simulation_Lab.py** — Isolated simulated scenarios (`simulation_*` tables only). Uses `src.database`, `src.ui_components`.
9. **9_Model_Performance.py** — Displays evaluation CSVs/JSONs from `research_reports/results/`. Uses `src.database`, `src.ui_components`.
10. **10_Reports_Export.py** — CSV/Excel/PDF export of DB records. Uses `src.database`, `src.ui_components`.
11. **11_Settings.py** — Persistent inference/map/risk settings in `app_settings`. Uses `src.database`, `src.ui_components`.

---

## 6. DATABASE (`SCHEMA_SQL` in `src/database.py`)

SQLite `data/roadintel.db`. Types as declared.

**detections:** id TEXT PK, created_at TEXT NOT NULL, source_name TEXT NOT NULL, source_type TEXT NOT NULL DEFAULT 'image', detection_index INTEGER NOT NULL DEFAULT 0, class_id INTEGER NOT NULL DEFAULT 0, class_name TEXT NOT NULL DEFAULT 'pothole', confidence REAL NOT NULL, x1/y1/x2/y2 INTEGER NOT NULL, image_width INTEGER, image_height INTEGER, frame_index INTEGER, timestamp_s REAL, conf_threshold REAL, iou_threshold REAL, imgsz INTEGER, severity TEXT, area_ratio REAL, notes TEXT, annotated_path TEXT.

**locations:** id TEXT PK, detection_id TEXT FK → detections(id) ON DELETE SET NULL, created_at TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, address TEXT, location_source TEXT NOT NULL DEFAULT 'manual' (`manual` \| `map_click` \| `geocoded` \| `gps`), area_name TEXT, notes TEXT.

**repair_tasks:** id TEXT PK, detection_id TEXT FK → detections(id) ON DELETE SET NULL, location_id TEXT FK → locations(id) ON DELETE SET NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending Verification', priority TEXT NOT NULL DEFAULT 'Medium', assigned_team TEXT, assigned_worker TEXT, due_date TEXT, est_cost REAL, actual_cost REAL, before_image TEXT, after_image TEXT, repair_notes TEXT, verified_by TEXT, verified_at TEXT, closed_at TEXT.

**repair_status_log:** id TEXT PK, task_id TEXT NOT NULL FK → repair_tasks(id) ON DELETE CASCADE, changed_at TEXT NOT NULL, from_status TEXT, to_status TEXT NOT NULL, changed_by TEXT, notes TEXT.

**simulation_runs:** id TEXT PK, created_at TEXT NOT NULL, name TEXT NOT NULL, description TEXT, config_json TEXT, result_summary TEXT.

**simulation_records:** id TEXT PK, run_id TEXT NOT NULL FK → simulation_runs(id) ON DELETE CASCADE, created_at TEXT NOT NULL, lat REAL, lon REAL, severity TEXT, status TEXT, est_cost REAL, days_to_repair INTEGER, area_name TEXT.

**app_settings:** key TEXT PK, value TEXT NOT NULL, updated_at TEXT NOT NULL.

Indexes: idx_detections_created, idx_detections_severity, idx_locations_detection, idx_repair_detection, idx_repair_status, idx_sim_records_run.

### Repair statuses (`VALID_STATUSES` in `src/database.py`)

Pending Verification, Verified, Assigned, In Progress, Repaired, Reverified, Closed, Rejected.

### Transitions

**Documented intended path** (`docs/REPAIR_WORKFLOW.md`, page 6 docstring): Pending Verification → Verified → Assigned → In Progress → Repaired → Reverified → Closed; any non-terminal → Rejected; Closed/Rejected terminal.

**Code:** `transition_repair_status` only checks `new_status in VALID_STATUSES`. No allowed-edge map. UI (`pages/6_Repair_Management.py`) selectbox is the full `VALID_STATUSES` list. Sequential workflow is **not enforced** in code.

---

## 7. FORMULAS

### Severity (`src/severity.py` + `config.py`)

- Weights default: `conf_weight = 0.55`, `area_weight = 0.45`. If image size unknown: conf_weight=1.0, area_weight=0.0, area_ratio=0.
- `area_ratio = box_area / image_area` (capped at 1.0).
- `area_score = min(area_ratio / 0.20, 1.0)`.
- `score = conf_weight * confidence + area_weight * area_score`.
- Thresholds (`config.py`): Critical ≥ 0.78; High ≥ 0.58; Medium ≥ 0.38; else Low.
- File comment: visual triage aid, not a validated safety prediction.

### Risk (`src/risk_score.py` + `config.py`)

```
R = w1 * norm(pothole_count)
  + w2 * norm(avg_severity_value)
  + w3 * norm(recurrence_rate)
  + w4 * norm(age_days_unresolved)
```

Weights (`config.py` / function defaults): count 0.30, severity 0.30, recurrence 0.20, age 0.20. Then divide by sum of weights; scale `min(score,1)*100`.

Severity numeric: Low=1, Medium=2, High=3, Critical=4.

Risk labels: ≥75 Very High; ≥50 High; ≥25 Moderate; else Low.

---

## 8. STACK

`requirements.txt` (exact):

```
streamlit>=1.35.0
ultralytics>=8.3.0
opencv-python-headless>=4.9.0
Pillow>=10.0.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
folium>=0.16.0
streamlit-folium>=0.20.0
openpyxl>=3.1.0
fpdf2>=2.7.0
geopy>=2.4.0
pytest>=8.0.0
```

- Project venv Python: **3.13.2** (`.venv/pyvenv.cfg`).
- Host `python --version` on this machine: 3.14.7 (not the venv used by the app).
- OS: Windows NT 10.0.26300.0 (`[System.Environment]::OSVersion`).

---

## 9. CODE METRICS

Command: PowerShell `Get-ChildItem … -Filter *.py|*.md` then `Get-Content | Measure-Object -Line`. **Non-blank lines only.** Excluded `.venv`, `__pycache__`, `.pytest_cache`.

| Group | Files | Non-blank lines |
|---|---|---|
| `src/*.py` | 10 | 2020 |
| `pages/*.py` | 11 | 3494 |
| `tests/*.py` | 2 | 189 |
| `docs/*.md` | 12 | 1162 |
| root `app.py` | 1 | 171 |
| root `config.py` | 1 | 73 |
| root py total | 2 | 244 |

Per-file src: database.py 711, ui_components.py 527, video_inference.py 195, risk_score.py 158, severity.py 110, image_inference.py 106, reporting.py 93, model_loader.py 66, validation.py 53, __init__.py 1.

Per-file pages: 8_Simulation_Lab.py 467, 10_Reports_Export.py 465, 4_GIS_Map.py 428, 2_Live_Detection.py 397, 6_Repair_Management.py 372, 11_Settings.py 328, 9_Model_Performance.py 301, 1_Executive_Overview.py 278, 7_Advanced_Analytics.py 196, 5_Road_Condition_Intelligence.py 151, 3_Detection_History.py 111.

Tests: test_reporting.py 111, test_validation.py 78.

---

## 10. TESTS

Command: `.\.venv\Scripts\python.exe -m pytest -q` in `pothole-detection-system`. Finished **0.09s**.

Summary line: **`29 passed in 0.09s`**

---

## 11. DATA IN DB (`data/roadintel.db`)

Counts: detections **11**, locations **1**, repair_tasks 0, repair_status_log 0, simulation_runs 0, simulation_records 0, app_settings 0.

| id | severity | confidence | source_name | source_type |
|---|---|---|---|---|
| 52ee4b89-8868-4415-b75c-4507fa327ef5 | Medium | 0.7593 | Screenshot 2026-10-13 110232.png | image |
| 93318253-24e2-46ee-b498-7507cd773ca4 | Medium | 0.7593 | Screenshot 2026-10-13 110232.png | image |
| b9e55ec6-142a-459d-b788-a62efe0d62fb | Medium | 0.7593 | Screenshot 2026-10-13 110232.png | image |
| 1efdaa69-739a-437e-b64b-4d7f889a4a3c | Medium | 0.7593 | Screenshot 2026-10-13 110232.png | image |
| 221b736d-ca7d-4919-a97c-2cad800a8697 | Medium | 0.8731 | potholes0.png | demo |
| ff344060-3b05-4bae-9718-97c66329b34a | Medium | 0.8552 | potholes0.png | demo |
| feea0aae-1611-400c-9c47-83ce1c306396 | Medium | 0.7988 | potholes0.png | demo |
| ae3ef95e-5c4b-4219-9c0d-4e4c5afc5c4e | Medium | 0.7647 | potholes0.png | demo |
| dd1a9317-f87d-47f4-aebf-08f534df4e7f | Low | 0.6229 | potholes0.png | demo |
| adf7469c-4b39-4541-b55d-068d19e65cee | Low | 0.5581 | potholes0.png | demo |
| 21ceecce-6813-4356-a9b1-c6e258aba475 | Low | 0.4575 | potholes0.png | demo |

All 11: imgsz 800, conf_threshold 0.45, iou_threshold 0.45, created 2026-10-30 ~22:02–22:03 UTC.

**How lat/lon were set:** 10 of 11 have **no** location row. One location: detection `b9e55ec6-…`, **lat 15.6, lon 15.65**, address null, **`location_source = 'manual'`**, area_name null. Not `gps`, not `geocoded`, not `map_click`. Code does not auto-generate GPS (`docs/MAP_MODULE.md`: “GPS fabrication is strictly prohibited”). Coordinates 15.6, 15.65 look like a typed test pair, not a surveyed Indian road GPS. First four detections are four saves of the same screenshot at identical confidence 0.7593. Seven rows are `source_type='demo'` from bundled `potholes0.png`. **Look like demonstration / test data, not a field survey.**

---

## 12. LIMITATIONS (only those in code/docs)

From README.md, RESULTS_AND_LIMITATIONS.md, PROJECT_REPORT.md, METHODOLOGY.md, MAP_MODULE.md, SIMULATION.md, severity.py, risk_score.py, app:

- Single class `pothole`.
- Dataset 665 images; limited geography / quality variation.
- Physical depth/severity cannot be measured from monocular RGB; severity is a bbox-area + confidence proxy, unvalidated.
- Risk score is a prioritisation aid, not a validated safety model.
- GPS not captured from images; location only if user provides it.
- Geocoding uses Nominatim and needs internet (`pages/4_GIS_Map.py`, Settings geocoding checkbox).
- Simulation data isolated; must not be mixed with real dashboards (`pages/8_Simulation_Lab.py`).
- No trained segmentation model.
- CPU inference at imgsz=800 can be slow (seconds/image, minutes/video).
- Validation metrics are not independent test performance (`model_metadata.json` warning).
- Older docs still say YOLO11n-800 test metrics / FP-FN “not verified” even though `final_test_comparison/` files exist.
- **No authentication / login** in project `src/` or `pages/` (no `st.login`, no password gate). Not stated as a sentence in `docs/`, but no auth code is present.
- Repair status transitions not constrained to the documented sequence (`src/database.py`).
- SQLite, local-only; README: no data uploaded externally (`app.py` caption).

---

## 13. DOCS (12 files under `docs/`)

| File | Title (first heading) |
|---|---|
| PROJECT_REPORT.md | Project Report: AI-Based Road Pothole Detection System |
| METHODOLOGY.md | Methodology |
| RESULTS_AND_LIMITATIONS.md | Results and Limitations |
| FEATURES.md | RoadSight Intelligence Platform v2.0 — Features Guide |
| TESTING.md | Testing Documentation |
| ANALYTICS.md | Analytics Module Documentation |
| MAP_MODULE.md | GIS Map Module Documentation |
| SIMULATION.md | Simulation Lab Documentation |
| REPAIR_WORKFLOW.md | Repair Workflow Documentation |
| DEMONSTRATION_GUIDE.md | Demonstration Guide |
| UPGRADE_PLAN.md | RoadSight Intelligence Platform v2.0 — Upgrade Plan |
| UPGRADE_AUDIT.md | RoadSight Intelligence Platform v2.0 — Upgrade Audit |

No `References` / bibliography / citation list file found in `docs/`.

---

## 14. UNKNOWN / [TO CONFIRM]

- Student name, roll number, guide name, academic year.
- Whether HOD is still Prof. A. M. Bainwad (not in repo).
- Whether a project logo or title-page image is required.
- Commercial target users, selling price, municipal cost figures (only in-app default repair costs exist).
- Dataset licence and named public source URL.
- Train-split instance count.
- Parameter count / GFLOPs of YOLO11n checkpoint.
- Confidence, NMS IoU stored **inside** `final_model_comparison.json` (absent; methodology says 0.45 / 0.45 / matching 0.50).
- NMS IoU inside `final_test_comparison/*.json` (absent; Confidence 0.4 is stored).
- How to reconcile older “YOLO11n-800 test metrics not available” docs vs `final_test_comparison/` files (both exist; report writer must choose wording).
- Installed pinned versions in venv (only lower bounds in requirements.txt were copied; `pip freeze` not run to stay under time / avoid extra jobs).
