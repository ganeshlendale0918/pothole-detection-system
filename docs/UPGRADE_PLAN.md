# RoadSight Intelligence Platform v2.0 — Upgrade Plan

## Objective
Transform the existing Streamlit pothole detection demo into a professional
Road Intelligence & Monitoring Platform with 11 specialized pages.

## Architecture (Implemented)

```
pothole-detection-system/
├── app.py                          # Entry point, model cache, sidebar nav, landing page
├── config.py                       # Centralised config (paths, thresholds, defaults)
├── requirements.txt                # Python dependencies
├── data.yaml                       # YOLO dataset spec (reference only)
│
├── models/
│   ├── best.pt                     # Primary YOLO11n checkpoint (never modified)
│   ├── model_metadata.json         # Inference defaults and dataset info
│   ├── yolo11n_640.pt              # Baseline comparison model
│   └── yolov8n_640.pt              # Baseline comparison model
│
├── src/
│   ├── database.py                 # Full SQLite data layer (7 tables)
│   ├── model_loader.py             # Cached YOLO model loader
│   ├── image_inference.py          # Image detection pipeline
│   ├── video_inference.py          # Video frame extraction + inference
│   ├── severity.py                 # Area-ratio → severity classification
│   ├── risk_score.py               # Area-level risk scoring
│   ├── ui_components.py            # Reusable CSS + Streamlit components
│   ├── reporting.py                # CSV/JSON export utilities
│   └── validation.py               # Model path validation
│
├── pages/
│   ├── 1_Executive_Overview.py     # KPI dashboard, charts, activity feed
│   ├── 2_Live_Detection.py         # Image/video inference, save results
│   ├── 3_Detection_History.py      # Paginated history with filters
│   ├── 4_GIS_Map.py                # Interactive Folium map, location management
│   ├── 5_Road_Condition_Intelligence.py  # Risk scoring, area analysis
│   ├── 6_Repair_Management.py      # Full repair lifecycle
│   ├── 7_Advanced_Analytics.py     # Interactive Plotly analytics
│   ├── 8_Simulation_Lab.py         # ★ NEW — Isolated scenario simulation
│   ├── 9_Model_Performance.py      # ★ NEW — Model evaluation center
│   ├── 10_Reports_Export.py        # ★ NEW — Reports and export
│   └── 11_Settings.py              # ★ NEW — Persistent platform settings
│
├── data/
│   ├── roadintel.db                # SQLite database (auto-created)
│   ├── uploads/                    # Uploaded image/video files
│   └── repair_images/              # Before/after repair photos
│
├── docs/                           # ★ NEW — Full documentation suite
│   ├── UPGRADE_AUDIT.md
│   ├── UPGRADE_PLAN.md
│   ├── FEATURES.md
│   ├── MAP_MODULE.md
│   ├── REPAIR_WORKFLOW.md
│   ├── ANALYTICS.md
│   ├── SIMULATION.md
│   └── TESTING.md
│
├── research_reports/
│   └── results/                    # Real evaluation CSVs/JSONs (never modified)
│
├── assets/
│   └── sample_images/              # Sample pothole images
│
└── tests/                          # pytest test suite
```

## Database Schema

7 tables:
1. `detections` — inference results
2. `locations` — optional GPS/coordinates
3. `repair_tasks` — repair lifecycle
4. `repair_status_log` — immutable audit trail
5. `simulation_runs` — isolated scenario metadata
6. `simulation_records` — isolated simulated potholes
7. `app_settings` — persistent key-value config

## UI Design System

- **Theme:** Premium dark dashboard
- **Font:** Inter (Google Fonts)
- **Accent:** Indigo/Purple/Pink gradient palette
- **Components:** KPI cards, glass cards, hero banners, severity pills, status pills
- **Charts:** Plotly dark theme with transparent backgrounds
- **Map:** Folium + streamlit-folium, severity-coloured markers

## Non-Negotiable Rules (All Satisfied)

1. ✅ Upgrade existing app — no reconstruction
2. ✅ Model weights preserved (`models/best.pt` unchanged)
3. ✅ Inference pipeline preserved
4. ✅ Existing functionality preserved (pages 1–7)
5. ✅ No fabricated real-world data
6. ✅ No fabricated GPS locations
7. ✅ Simulated data strictly isolated
8. ✅ Persistent SQLite storage for all real records
9. ✅ No silent model configuration changes
10. ✅ No automatic retraining
11. ✅ All 11 pages fully implemented

## Dependencies Added

| Package | Reason |
|---------|--------|
| `folium>=0.16` | Interactive map rendering |
| `streamlit-folium>=0.20` | Folium ↔ Streamlit bridge |
| `openpyxl>=3.1` | Excel export (XLSX) |
| `fpdf2>=2.7` | PDF report generation |
| `geopy>=2.4` | Address geocoding |

All installed in virtual environment without affecting existing packages.
