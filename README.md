# 🛣️ RoadSight Intelligence Platform v2.0

> AI-powered road pothole detection, geospatial analytics, and repair lifecycle management.
> Built as a college academic project using YOLO11n, Streamlit, SQLite, and Folium.

[![Live App](https://img.shields.io/badge/🌐%20Live%20App-roadsight.streamlit.app-4f46e5?style=for-the-badge)](https://roadsight.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![YOLO](https://img.shields.io/badge/Model-YOLO11n-00DCFA?style=flat)](https://ultralytics.com)

---

## 🌐 Live Demo

**https://roadsight.streamlit.app/**

> ⚠️ **First-load note:** The app is hosted on Streamlit Community Cloud (free tier). If it shows a *"This app has gone to sleep"* screen, click **"Yes, get this app back up!"** and wait up to **60 seconds**. Subsequent navigation is fast.
>
> No login or registration required — the app is fully open.

---

## 📌 Project Overview

RoadSight Intelligence Platform v2.0 is a full-stack AI application that:

1. **Detects potholes** in uploaded road images and videos using a custom-trained YOLO11n model (trained on 665 annotated road images, mAP@50 = 86.97% on validation set).
2. **Classifies severity** (Low / Medium / High / Critical) based on bounding box area relative to image size.
3. **Pins locations** on an interactive OpenStreetMap via manual coordinates, address geocoding, or map-click.
4. **Manages repairs** through a full lifecycle: Pending Verification → Verified → Assigned → In Progress → Repaired → Reverified → Closed.
5. **Generates reports** (CSV, Excel, JSON, GeoJSON) from real database records.
6. **Simulates scenarios** in a fully isolated lab that never contaminates real data.

---

## ✨ Features (12 Pages)

| Page | Feature |
|---|---|
| 🏠 Home | Live platform KPIs, feature overview |
| 📊 Executive Overview | Detection timeline, severity distribution, repair status charts, mini GIS map |
| 🔍 Live Detection | Image upload, video upload, demo sample inference; confidence/IoU/size controls; DB save |
| 📋 Detection History | Searchable, filterable table of all saved detections |
| 🗺️ GIS Map | Interactive Folium map; manual/geocoded/map-click location entry; heatmap; cluster markers |
| 🛣️ Road Condition Intelligence | Area-wise risk scoring and road condition classification |
| 🔧 Repair Management | Full lifecycle task manager; before/after images; status history timeline; overdue alerts |
| 📈 Advanced Analytics | Plotly dashboards: trends, area breakdowns, severity, repair KPIs, cost tracking |
| 🔬 Simulation Lab | Isolated scenario modelling; configurable potholes, budget, strategy; scenario comparison |
| 🏆 Model Performance | Real evaluation metrics from `research_reports/results/`; YOLO11n vs YOLOv8n vs DETR-R50 |
| 📤 Reports & Export | Detection, severity, location, repair, cost, and model reports; CSV, Excel, JSON, GeoJSON |
| ⚙️ Settings | Platform configuration |

---

## 🏗️ Architecture

```
pothole-detection-system/
├── app.py                        ← Home page & model loader
├── config.py                     ← Paths, defaults, constants
├── requirements.txt
├── packages.txt                  ← System deps for Streamlit Cloud
│
├── pages/                        ← 11 additional Streamlit pages
│   ├── 1_Executive_Overview.py
│   ├── 2_Live_Detection.py
│   ├── 3_Detection_History.py
│   ├── 4_GIS_Map.py
│   ├── 5_Road_Condition_Intelligence.py
│   ├── 6_Repair_Management.py
│   ├── 7_Advanced_Analytics.py
│   ├── 8_Simulation_Lab.py
│   ├── 9_Model_Performance.py
│   ├── 10_Reports_Export.py
│   └── 11_Settings.py
│
├── src/
│   ├── database.py               ← SQLite schema, all DB operations
│   ├── model_loader.py           ← Cached YOLO11n loading
│   ├── image_inference.py        ← Image inference pipeline
│   ├── video_inference.py        ← Frame-by-frame video pipeline
│   ├── severity.py               ← Severity classification logic
│   ├── risk_score.py             ← Area risk scoring
│   ├── reporting.py              ← CSV/JSON export utilities
│   ├── ui_components.py          ← Shared hero banners, cards, CSS
│   └── validation.py             ← Input validation helpers
│
├── models/
│   ├── best.pt                   ← Custom YOLO11n checkpoint (required)
│   └── model_metadata.json       ← Inference defaults and model info
│
├── assets/
│   └── sample_images/            ← Bundled demo images
│
├── data/
│   ├── roadintel.db              ← SQLite database (auto-created)
│   └── repair_images/            ← Before/after repair photos
│
├── research_reports/
│   └── results/                  ← Verified experiment CSVs/JSONs
│
├── docs/                         ← All project documentation
│   ├── TEACHER_EVALUATION_GUIDE.md
│   ├── PROJECT_REPORT.md
│   ├── METHODOLOGY.md
│   ├── RESULTS_AND_LIMITATIONS.md
│   └── ...
│
└── tests/
    ├── test_validation.py
    └── test_reporting.py
```

---

## 📊 Model & Dataset

| Property | Value |
|---|---|
| Architecture | YOLO11n (Ultralytics) |
| Training platform | Google Colab |
| Pretrained base | COCO |
| Inference image size | 800 px |
| Default confidence | 0.45 |
| Default IoU/NMS | 0.45 |
| Detection classes | `pothole` (class ID 0) |
| Total dataset images | 665 |
| Training split | 532 |
| Validation split | 66 |
| Test split | 67 |
| Annotation format | Pascal VOC XML → YOLO |

**Evaluation Metrics:**

| Metric | Validation Set | Test Set (independent) |
|---|---|---|
| mAP@50 | **86.97%** | **78.05%** |
| mAP@50-95 | **58.67%** | **49.31%** |

> ⚠️ Validation-set figures come from the training audit. Test-set figures are from an independent evaluation on 67 held-out images.

---

## 🚀 Local Installation (Optional)

The app runs live at https://roadsight.streamlit.app/ — local installation is only needed for development or if the cloud app is unavailable.

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

> If PowerShell blocks activation:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

---

## 🗄️ Database

All real data is stored in `data/roadintel.db` (SQLite, auto-created on first run).

| Table | Contents |
|---|---|
| `detections` | All pothole detection records |
| `locations` | GIS map pins (lat, lon, area, address, source) |
| `repair_tasks` | Full repair lifecycle records |
| `repair_status_log` | Audit trail of all status transitions |
| `simulation_runs` | Saved simulation scenarios (isolated) |
| `simulation_records` | Simulated pothole records (never mixed with real data) |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| App sleeping on Streamlit Cloud | Click "Wake up" and wait 60 seconds |
| `Model checkpoint not found` | Ensure `models/best.pt` exists |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Video codec error | Convert video to MP4 H.264 using VLC or ffmpeg |
| Very slow video processing | Reduce the frame limit slider (keep ≤ 50 for demos) |
| Geocoding returns no result | Add city and country to the address query |

---

## ⚠️ Limitations

- Only one class (`pothole`) is detected — road cracks or markings are not classified.
- Pothole depth cannot be estimated from a 2D image; severity is based on bounding box area ratio.
- GPS coordinates must be entered manually or resolved via geocoding — no live GPS integration.
- Trained on 665 images; performance on unusual road types or lighting conditions may vary.
- No user authentication or role-based access control in this version.

---

## 🔮 Future Work

- Instance segmentation using YOLO11n-Seg for exact pothole outlines
- Larger, geographically diverse training dataset
- Mobile companion app with live GPS tagging
- Real-time CCTV/dashcam stream processing
- Role-based login (field worker, supervisor, admin)
- Automated weekly PDF report emails

---

## 📄 Documentation

All project documents are in the `docs/` folder:

| Document | Purpose |
|---|---|
| `TEACHER_EVALUATION_GUIDE.md` | Step-by-step guide for evaluators |
| `PROJECT_REPORT.md` | Full academic project report |
| `METHODOLOGY.md` | Training and evaluation methodology |
| `RESULTS_AND_LIMITATIONS.md` | Honest performance analysis |
| `FEATURES.md` | Detailed feature descriptions |

---

## 🧪 Running Tests

```powershell
pytest tests/ -v
```

Tests cover: file-extension validation, model-path validation, detection-record schema, CSV generation, JSON summary, and filename sanitisation.

---

*RoadSight Intelligence Platform v2.0 · YOLO11n · Academic Project*
