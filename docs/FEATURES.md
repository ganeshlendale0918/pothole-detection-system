# RoadSight Intelligence Platform v2.0 — Features Guide

## Platform Overview
RoadSight Intelligence Platform is an advanced AI-powered road monitoring system built on
Streamlit with a custom-trained YOLO11n pothole detection model.

---

## Page 1: Executive Overview
**URL:** `/1_Executive_Overview`

- Real-time KPI dashboard (total detections, today, high-severity, repair progress, cost)
- Detection timeline area chart (last 30 days)
- Severity distribution donut chart
- Repair status bar chart
- Recent detection activity feed
- Recent repair task table
- Date range filters
- Optional auto-refresh (30-second interval)

**Data source:** Live SQLite database — no fabricated values.

---

## Page 2: Live Detection Center
**URL:** `/2_Live_Detection`

- Upload image or video files
- Adjustable confidence threshold slider
- Adjustable IoU/NMS threshold slider
- Adjustable inference image size
- Original vs annotated image comparison
- Per-detection confidence labels and bounding boxes
- Severity classification per detection
- Processing time and FPS measurement
- Save detection results to database (with unique UUID)
- Frame-by-frame video processing with progress tracking
- CSV and JSON export of detection results

**Model:** YOLO11n from `models/best.pt` — loaded once, cached across all pages.

---

## Page 3: Detection History
**URL:** `/3_Detection_History`

- Paginated table of all saved detections
- Filter by severity, source type, date range, text search
- Download filtered results as CSV
- Delete individual detection records
- View annotated image for any saved detection count

---

## Page 4: GIS Map
**URL:** `/4_GIS_Map`

- Interactive Folium map with all potholes that have saved coordinates
- Add location by address (Nominatim geocoding — requires internet)
- Add location by manual latitude/longitude entry
- Click-to-select location on map
- Link locations to existing detection records
- Severity-coloured markers (Red = Critical, Orange = High, Yellow = Medium, Green = Low)
- Marker clustering for dense areas
- Interactive popups with detection details
- Heatmap toggle
- Filter by severity, date range, location source
- Distinction between GPS, geocoded, manual, and map-click sources
- Export location data as CSV or GeoJSON

---

## Page 5: Road Condition Intelligence
**URL:** `/5_Road_Condition_Intelligence`

- Area-level risk scores computed from real detection records
- Risk formula: count + severity + recurrence + age (configurable weights)
- High-risk area ranking table
- Area-wise pothole density visualisation
- Severity distribution by area
- Detection frequency trends
- Transparent risk formula documentation
- Disclaimer: prioritisation aid, not safety prediction

---

## Page 6: Repair & Maintenance Management
**URL:** `/6_Repair_Management`

**Lifecycle:**  
Pending Verification → Verified → Assigned → In Progress → Repaired → Reverified → Closed  
*(Rejection available at any stage)*

**Features:**
- KPI strip (total tasks, pending, in-progress, completed, overdue, estimated cost)
- Overdue alert banner
- Task list with status/priority filters
- Create repair task (link to detection, set priority, team, worker, due date, estimated cost)
- Task detail view with full field display
- Status transitions with audit logging
- Actual cost entry
- Status history timeline view
- CSV export of task list
- All changes persisted in SQLite (not just session state)

---

## Page 7: Advanced Analytics
**URL:** `/7_Advanced_Analytics`

- Daily detection trend bar charts with date filter
- Severity-stacked daily detection chart
- Detection confidence histogram
- Confidence vs area-ratio scatter (coloured by severity)
- Area-wise detection bar chart (from location area_name)
- Repair status donut chart
- Repair priority distribution
- Estimated vs actual cost scatter
- Download individual chart data as CSV
- Full Excel export (detections + repair tasks on separate sheets)

**All charts:** Connected to real database records only.

---

## Page 8: Simulation & Scenario Lab
**URL:** `/8_Simulation_Lab`

> ⚠️ ALL data on this page is SIMULATED. Never contaminates real records.

**Configure:**
- Number of potholes (10–2,000)
- Detection period (days)
- Severity distribution sliders (Low / Medium / High / Critical %)
- Geographic areas (select from template list + add custom)
- Repair team capacity (jobs/day)
- Average repair duration (days)
- Total repair budget
- Repair prioritisation strategy:
  - Priority (Highest Severity First)
  - Priority (Lowest Cost First)
  - Geographic Clustering
  - FIFO

**Scenario Results:**
- KPI strip (total potholes, critical count, repaired, repair rate, costs)
- Severity distribution donut [SIMULATED]
- Repair status outcomes bar [SIMULATED]
- Simulated daily detection trend area chart [SIMULATED]
- Area-wise pothole count bar [SIMULATED]
- Budget usage pie [SIMULATED]
- Workload projection narrative
- Export: CSV and JSON

**Saved Scenarios:**
- Save scenarios to database (simulation_runs table)
- View all saved scenarios with key metrics
- Download individual scenario records as CSV
- Delete scenarios

**Compare Scenarios:**
- Side-by-side grouped bar chart of any two saved scenarios
- Comparison table

---

## Page 9: Model Performance Center
**URL:** `/9_Model_Performance`

- Primary model KPI strip (Precision, Recall, F1, mAP@50, mAP@50-95, Inference time, Est. FPS)
- Model comparison: YOLO11n vs YOLOv8n vs DETR-R50
- Radar chart (multi-metric comparison)
- Grouped bar chart (per-metric by model)
- Dataset statistics (split sizes, annotation format)
- Dataset split pie chart
- Model specification card
- Experiment results table (from experiment_results.csv)
- Training audit log (from phase63_training_audit.csv)
- Operational inference statistics from live database:
  - Confidence histogram
  - Operational severity distribution
  - Detections by source type
- Metric disclaimer banner

**Data sources:** All metrics from `research_reports/results/` files — no fabricated values.

---

## Page 10: Reports & Export Center
**URL:** `/10_Reports_Export`

**Report Types:**
1. Detection Summary — count, avg/min/max confidence, paginated table
2. Severity Report — count, percentage, estimated cost by severity
3. Location Report — all geocoded locations with GeoJSON export
4. Repair Progress Report — status distribution, completion rate, task table
5. Cost Report — estimated vs actual costs, by priority breakdown
6. Model Evaluation Report — text report from evaluation files

**Export Formats:**
- CSV (per report)
- Excel (per report + full multi-sheet workbook)
- GeoJSON (locations)
- JSON bundle (all data, capped at 500 rows per table)

**Global Filters:** Date range + severity multi-select applied to all reports.

---

## Page 11: Settings
**URL:** `/11_Settings`

**Tabs:**
1. **Inference** — Default confidence, IoU threshold, image size, max video frames
2. **Map** — Default lat/lon/zoom, geocoding enable/disable
3. **Risk Scoring** — Configurable weights (count/severity/recurrence/age), severity thresholds
4. **Display** — Auto-refresh interval, records per page, cost currency symbol
5. **Data Management** — Database stats, file paths, size info, safety notices
6. **About** — Platform info, model specs, technology stack, non-negotiable rules

All settings are persisted in the `app_settings` SQLite table and survive restarts.

---

## Navigation Structure

```
🏠 Home (app.py)
├── 📊 Executive Overview
├── 🔍 Live Detection Center
├── 📋 Detection History
├── 🗺️ GIS Map
├── 🛣️ Road Condition Intelligence
├── 🔧 Repair & Maintenance Management
├── 📈 Advanced Analytics
├── 🔬 Simulation & Scenario Lab
├── 🏆 Model Performance Center
├── 📤 Reports & Export Center
└── ⚙️ Settings
```

---

## Design System

- **Theme:** Dark professional — `#0a0a1a` → `#0f0c29` gradient background
- **Typography:** Inter (Google Fonts) — 300/400/500/600/700/800 weights
- **Accent palette:** Indigo (#6366f1), Purple (#8b5cf6), Pink (#ec4899)
- **Severity colours:** Critical=#ef4444, High=#f97316, Medium=#eab308, Low=#22c55e
- **Status colours:** On=green, In-progress=amber, Error=red, Info=blue, Sim=purple
- **Components:** KPI cards, glass cards, severity pills, status pills, hero banners, info boxes
- **Charts:** Plotly with transparent backgrounds, dark theme, indigo colour sequences
