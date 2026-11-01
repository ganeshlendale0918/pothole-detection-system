# RoadSight Intelligence Platform v2.0 — Teacher Evaluation Guide

> 🌐 **Live Deployment URL:** **https://roadsight.streamlit.app/**
> 🏠 **Local Fallback URL:** `http://localhost:8501` *(if the cloud app is unavailable)*
> 🔓 **Demo Account:** No login is required. The application is open to all users.
> ⚠️ **Important — First Load Warning:** This application is hosted on Streamlit Community Cloud (free tier). If the app has not been visited recently, it may show a **"This app is sleeping"** screen. Click the **"Wake up"** button and wait up to **60 seconds** for the app to become active. Subsequent page loads within the same session are fast.
> 📅 **Date Prepared:** 1 November 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [How to Access the Project](#2-how-to-access-the-project) — **Start here: use the live URL**
3. [Feature Checklist (Summary Table)](#3-feature-checklist-summary-table)
4. [How to Test Each Feature](#4-how-to-test-each-feature)
5. [Quick Demo Flow (5 Minutes)](#5-quick-demo-flow-5-minutes)
6. [Technology and Structure](#6-technology-and-structure)
7. [Limitations and Future Improvements](#7-limitations-and-future-improvements)
8. [Contact](#8-contact)

---

## 1. Project Overview

**RoadSight Intelligence Platform v2.0** is an AI-powered web application built to detect and manage road potholes. The system uses a custom-trained YOLO11n deep-learning model (trained on 665 annotated road images) to automatically identify potholes in uploaded photographs and videos.

Beyond detection, the platform provides a complete operational workflow: detected potholes can be pinned on an interactive geographic map, repair tasks can be created and tracked through a structured lifecycle (Pending → Verified → Assigned → In Progress → Repaired → Closed), and all results are stored in a local SQLite database. The platform also includes advanced analytics dashboards, a model performance audit page, hypothetical scenario simulation, and one-click report export in CSV, Excel, and JSON formats.

---

## 2. How to Access the Project

### Option A — Live Cloud Deployment (Recommended)

1. Open **Google Chrome** or **Microsoft Edge**.
2. Visit: **https://roadsight.streamlit.app/**
3. If the screen shows **"This app has gone to sleep"**, click the **"Yes, get this app back up!"** button.
4. Wait up to **60 seconds** for the app to wake up. This delay only happens once per session.
5. The application will open directly — no login or registration is needed.

> **Why the delay?** The app is hosted on Streamlit Community Cloud's free tier. Free apps automatically sleep after periods of inactivity to save resources. Once awake, the app responds instantly.

---

### Option B — Local Installation (Fallback)

Use this option only if the cloud URL is unavailable.

**Step 1 — Open PowerShell** on the project computer.

**Step 2 — Navigate to the project folder:**
```
cd "d:\Coding\A-PROJECTS\Pothole_Submission\pothole-detection-system"
```

**Step 3 — Activate the virtual environment:**
```
.\.venv\Scripts\Activate.ps1
```

> If activation is blocked, run this first:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

**Step 4 — Start the application:**
```
streamlit run app.py
```

**Step 5 — Open in a browser:** Visit **http://localhost:8501**

> **No login or registration is required.** The application opens directly to the Home page.

### What the Teacher Should See on the First Screen

The Home page will display:
- The **RoadSight Intelligence Platform** title banner with a road icon (🛣️)
- A row of **five platform summary metrics** (total detections, today's detections, high/critical potholes, repair tasks, completion rate)
- A grid of **six feature cards** describing the main capabilities
- A **sidebar on the left** listing navigation links to all 12 pages

[Insert screenshot: Home page — hero banner and metric row]

### If the Page Loads Slowly or Shows an Error

| Symptom | What to Do |
|---|---|
| Blank page for more than 30 seconds | Wait — the AI model is loading for the first time. This is normal. |
| "Model unavailable" warning in the sidebar | The file `models/best.pt` may be missing. Contact the student. |
| `ModuleNotFoundError` in the terminal | Run `pip install -r requirements.txt` and restart. |
| Port already in use | Run `streamlit run app.py --server.port 8502` and visit `http://localhost:8502` |

---

## 3. Feature Checklist (Summary Table)

| No. | Feature | Where to Find It | Pass / Fail |
|-----|---------|-----------------|-------------|
| 1 | Home page with live KPI metrics | Home page (app.py) | |
| 2 | Image upload and pothole detection | Sidebar → 🔍 Live Detection → Image Detection tab | |
| 3 | Video upload and frame-by-frame detection | Sidebar → 🔍 Live Detection → Video Detection tab | |
| 4 | Demo mode (no upload needed) | Sidebar → 🔍 Live Detection → Demo Samples tab | |
| 5 | Detection results saved to database | Live Detection → "Save results to database" checkbox | |
| 6 | Confidence, IoU, and image size controls | Sidebar sliders on the Live Detection page | |
| 7 | Download annotated image/CSV/JSON | Live Detection → Downloads section (after detection) | |
| 8 | Executive Overview dashboard | Sidebar → 📊 Executive Overview | |
| 9 | Detection activity timeline chart | Executive Overview page | |
| 10 | Severity distribution chart | Executive Overview page | |
| 11 | Detection History table | Sidebar → 📋 Detection History | |
| 12 | Interactive GIS map with markers | Sidebar → 🗺️ GIS Map → Map View tab | |
| 13 | Add location manually (lat/lon) | GIS Map → Add Location → Manual Lat/Lon tab | |
| 14 | Geocode a location by address | GIS Map → Add Location → Address Geocoding tab | |
| 15 | Add location by clicking the map | GIS Map → Add Location → Map Click tab | |
| 16 | Density heatmap on GIS map | GIS Map → Map View → Map Filters → "Show density heatmap" | |
| 17 | Create a repair task | Sidebar → 🔧 Repair Management → Create Task tab | |
| 18 | Update repair task status | Repair Management → Task Detail & Update tab | |
| 19 | Before/after image upload for repair | Repair Management → Task Detail & Update → Before/After Images | |
| 20 | Status history timeline | Repair Management → Task Detail & Update → Status History | |
| 21 | Repair KPI dashboard | Repair Management — top of the page | |
| 22 | Overdue task alerts | Repair Management — banner appears if tasks are overdue | |
| 23 | Advanced analytics charts | Sidebar → 📈 Advanced Analytics | |
| 24 | Scenario simulation (isolated) | Sidebar → 🔬 Simulation Lab → Configure Scenario tab | |
| 25 | Simulation results and export | Simulation Lab → Scenario Results tab | |
| 26 | Compare two simulated scenarios | Simulation Lab → Compare Scenarios tab | |
| 27 | Model performance metrics (real data) | Sidebar → 🏆 Model Performance | |
| 28 | Model comparison (YOLO11n vs others) | Model Performance → Model Comparison section | |
| 29 | Report generation and download | Sidebar → 📤 Reports & Export | |
| 30 | Full Excel multi-sheet export | Reports & Export → Full Export tab | |

---

## 4. How to Test Each Feature

---

### Feature 1 — Home Page with Live KPI Metrics

**Purpose:** Shows the platform's overall health at a glance using real database figures.

**Where to find it:** The Home page loads automatically when the application starts.

**Test steps:**
1. Open `http://localhost:8501` in the browser.
2. Look at the row of five numbered tiles beneath the hero banner.
3. Each tile should display a number (even if zero for a fresh install).

**Expected result:** Five metric tiles appear with labels: "Detections", "Today", "High / Critical", "Repair Tasks", and "Completion". All values are real figures from the database (zeros are correct for a fresh install).

**Common problems:**
- Metrics show an error: Ensure the application started without errors in the terminal.

---

### Feature 2 — Image Upload and Pothole Detection

**Purpose:** Allows the user to upload a road photograph; the AI model detects and highlights potholes with bounding boxes and confidence scores.

**Where to find it:** Sidebar → **🔍 Live Detection** → **Image Detection** tab.

**Test steps:**
1. Click **🔍 Live Detection** in the left sidebar.
2. Ensure the **Image Detection** tab is selected (it is the default).
3. Click **Browse files** and upload any road photograph in JPG, PNG, or WEBP format.
4. Wait for the spinner: "Running YOLO11n inference…"
5. Observe the results when the spinner disappears.

**Sample input:** Any road photograph from your phone or computer. A clear, daylight photo of a road surface works best.

**Expected result:**
- The original image appears on the left; the annotated image with bounding boxes appears on the right.
- A row of metric tiles shows: number of detections, inference time (in seconds), FPS, image size, and confidence threshold.
- A table below lists each detected pothole with its class name, confidence score, severity (Low / Medium / High / Critical), and bounding box coordinates.
- A confidence histogram chart is displayed.
- A green success message "✅ N detection(s) saved to database" appears.

**Common problems:**
- "No potholes detected": Lower the confidence slider in the sidebar (try 0.25) and re-upload the image.
- Spinner runs for more than 60 seconds: The model is loading for the first time; wait.

[Insert screenshot: Image Detection result — side-by-side comparison and detection table]

---

### Feature 3 — Video Upload and Frame-by-Frame Detection

**Purpose:** Processes uploaded road videos frame by frame and reports potholes found across all frames.

**Where to find it:** Sidebar → **🔍 Live Detection** → **Video Detection** tab.

**Test steps:**
1. Click the **Video Detection** tab on the Live Detection page.
2. Set the **Max frames to process** slider to **50** (to keep the demo time short).
3. Click **Browse files** and upload a short road video (MP4, AVI, or MOV, up to a few seconds long).
4. The video preview will appear. Click **🚀 Process Video**.
5. Watch the progress bar and frame counter.

**Sample input:** A short 3–5 second road video recorded on a phone. Limit frames to 50 for a faster demo.

**Expected result:**
- A progress bar fills from 0% to 100%.
- Metric tiles show: frames processed, total detections found, processing time, and source FPS.
- A bar chart shows "Detections per Frame" (how many potholes were found in each frame).
- A table shows the first 200 detection rows with frame index and timestamp.
- A "Download Annotated Video (MP4)" button appears.
- A success message confirms database saving.

**Common problems:**
- Processing is very slow: Keep the frame limit at 50 or below for demonstrations.
- "Video processing failed" error: Convert the video to MP4 format using VLC or a similar tool.

---

### Feature 4 — Demo Samples (No Upload Needed)

**Purpose:** Allows testing the AI model without needing to provide a personal photograph, using pre-loaded sample images.

**Where to find it:** Sidebar → **🔍 Live Detection** → **Demo Samples** tab.

**Test steps:**
1. Click the **Demo Samples** tab on the Live Detection page.
2. Select any image from the **"Select sample image"** dropdown.
3. Click **▶ Run Demo Inference**.
4. Observe the results.

**Expected result:** The original sample image and the annotated output with bounding boxes appear side by side. Metrics and a detection table are shown below.

**Common problems:**
- Dropdown shows "No sample images found": Ensure sample images exist in the `assets/sample_images/` folder inside the project.

---

### Feature 5 — Confidence, IoU, and Image Size Sliders

**Purpose:** Lets the evaluator control detection sensitivity without changing the underlying AI model.

**Where to find it:** Left sidebar sliders on the **Live Detection** page.

**Test steps:**
1. Navigate to **🔍 Live Detection**.
2. In the sidebar, locate three sliders: **Confidence threshold**, **IoU / NMS threshold**, **Inference image size**.
3. Drag the **Confidence threshold** slider to **0.25**.
4. Upload the same road image again and note whether more or fewer potholes are detected.

**Expected result:** Lowering the confidence threshold causes more (possibly weaker) detections to appear. Raising it causes fewer, but higher-confidence detections.

---

### Feature 6 — Download Annotated Image, CSV, and JSON

**Purpose:** Exports the detection results for offline use or further analysis.

**Where to find it:** Live Detection → **Downloads** section (appears after detection is complete).

**Test steps:**
1. After running image detection (Feature 2), scroll below the detection table.
2. Three download buttons appear: **Annotated Image (PNG)**, **Detections CSV**, and **JSON Summary**.
3. Click each download button and verify the file is saved to your computer.

**Expected result:**
- The PNG file opens in an image viewer and shows the annotated road image.
- The CSV file opens in Excel and shows one row per detected pothole.
- The JSON file contains a structured summary with confidence, inference time, and metadata.

---

### Feature 7 — Executive Overview Dashboard

**Purpose:** A real-time management dashboard that shows detection trends, repair status, and severity distribution using live database data.

**Where to find it:** Sidebar → **📊 Executive Overview**.

**Test steps:**
1. Click **📊 Executive Overview** in the sidebar.
2. Observe the two rows of metric tiles at the top (Detection Overview and Repair Overview).
3. Review the detection timeline chart on the left and the severity donut chart on the right.
4. Scroll down to see the repair status bar chart and the recent activity feed.
5. Click **🔄 Refresh Now** to reload the dashboard.

**Sample input to test filters:**
- Set the "From" date to one week ago and click Refresh Now.
- Select "Critical" and "High" from the Severity filter in the sidebar.

**Expected result:** The metrics and charts update to reflect only detections within the chosen date range and severity level. Charts render without errors. The "No Detection Data" placeholder appears only if the database is empty — run Live Detection first to populate it.

[Insert screenshot: Executive Overview — KPI row and timeline chart]

---

### Feature 8 — Detection History Table

**Purpose:** Shows all past detection records stored in the database, with sorting and filtering.

**Where to find it:** Sidebar → **📋 Detection History**.

**Test steps:**
1. Click **📋 Detection History** in the sidebar.
2. A table of all saved detections is displayed.
3. Use the filter controls at the top of the page (date range, severity) to narrow the list.

**Expected result:** A table with columns for timestamp, source file name, severity, confidence score, and source type. If no detections have been run yet, a "No detection records yet" empty-state message appears.

---

### Feature 9 — Interactive GIS Map

**Purpose:** Displays pothole locations on an OpenStreetMap map with colour-coded markers, clustering, and optional heatmap.

**Where to find it:** Sidebar → **🗺️ GIS Map** → **Map View** tab.

**Test steps:**
1. Click **🗺️ GIS Map** in the sidebar.
2. The **Map View** tab opens by default. An interactive map appears.
3. If there are saved locations, coloured markers appear (red = Critical, orange = High, beige = Medium, green = Low).
4. Click any marker to open a popup with severity, confidence, area name, address, and repair status.
5. Expand **Map Filters**, tick **"Show density heatmap"**, and observe the heat overlay.
6. Tick **"Enable marker clustering"** to group nearby markers.
7. Scroll below the map to see the statistics row (mapped count by severity).

**Expected result:** Markers appear on the map at any saved coordinates. Clicking a marker opens a popup with complete information. The heatmap overlay shows red areas where potholes are densest.

**Common problems:**
- Map is blank except for the base map: No locations have been saved yet. Follow Feature 10 to add one.

[Insert screenshot: GIS Map — markers with popup open]

---

### Feature 10 — Add a Pothole Location Manually

**Purpose:** Pins a pothole on the GIS map by entering GPS coordinates, searching by address, or clicking the map.

**Where to find it:** GIS Map → **Add Location** tab.

**Test steps (Manual entry method):**
1. Click **🗺️ GIS Map** in the sidebar, then click the **➕ Add Location** tab.
2. Click the **📍 Manual Lat/Lon** inner tab.
3. Enter **Latitude:** `12.971599` and **Longitude:** `77.594566` (Bengaluru, India).
4. Type an area name, for example: `MG Road`.
5. Optionally link to a recent detection using the dropdown.
6. Click **📍 Save Manual Location**.

**Expected result:** A green success message appears: "✅ Location saved: (12.97160, 77.59457)". Switch to the Map View tab — a new marker will be visible at Bengaluru.

**Test steps (Address Geocoding method):**
1. Click the **🏠 Address Geocoding** inner tab.
2. Type in the address field: `MG Road, Bangalore, India`.
3. Click **🔍 Search Address**.
4. The system returns the resolved address and coordinates.
5. Click **💾 Save Geocoded Location**.

**Expected result:** The address is resolved to coordinates via OpenStreetMap's free geocoding service. A marker is added to the map.

**Common problems:**
- "Address not found": Try adding the city and country to the address (e.g., "MG Road, Bangalore, India").
- Geocoding is slow: It requires an internet connection. Wait up to 15 seconds.

---

### Feature 11 — Create a Repair Task

**Purpose:** Creates a formal repair task linked to a pothole detection, with priority, team assignment, cost estimate, and due date.

**Where to find it:** Sidebar → **🔧 Repair Management** → **Create Task** tab.

**Test steps:**
1. Click **🔧 Repair Management** in the sidebar.
2. Click the **➕ Create Task** tab.
3. In the "Link to detection" dropdown, select any recent detection (e.g., the one from the image upload test).
4. Set **Priority** to `High`.
5. Enter **Assigned team:** `Ward 5 Repair Crew`.
6. Enter **Assigned worker:** `Rajan Kumar`.
7. Set **Estimated cost (₹)** to `4000`.
8. Set the due date to one week from today.
9. Click **✅ Create Repair Task**.

**Expected result:** A green message appears: "✅ Repair task created! Task ID: `xxxxxxxx`". The task is now visible in the Task List tab and on the Executive Overview.

---

### Feature 12 — Update Repair Task Status

**Purpose:** Moves a repair task through its lifecycle (Pending Verification → Verified → Assigned → In Progress → Repaired → Closed) and records who changed it and when.

**Where to find it:** Repair Management → **Task Detail & Update** tab.

**Test steps:**
1. Click the **🔍 Task Detail & Update** tab on the Repair Management page.
2. In the "Quick-select recent task" dropdown, choose the task created in Feature 11.
3. Under **Update Status**, change the dropdown to **In Progress**.
4. Type your name in **Changed by**: `Teacher Test`.
5. Add a note: `Repair crew dispatched`.
6. Click **💾 Save All Updates**.

**Expected result:** A green message "✅ Task updated → status: In Progress" appears. Scroll to the **Status History Timeline** below; a timeline entry is added showing the status transition, timestamp, and name.

---

### Feature 13 — Before and After Repair Images

**Purpose:** Allows uploading a photograph of the pothole before and after repair for visual documentation.

**Where to find it:** Repair Management → Task Detail & Update → **Before / After Images** section.

**Test steps:**
1. Open a repair task in the Task Detail & Update tab.
2. Under **Before repair image**, click **Browse files** and upload any photograph.
3. Under **After repair image**, click **Browse files** and upload another photograph.
4. Click **💾 Save All Updates**.

**Expected result:** Both images are saved and displayed in the Before/After panel the next time the task is opened.

---

### Feature 14 — Advanced Analytics Charts

**Purpose:** Interactive Plotly dashboards showing detection trends, area-wise breakdowns, and repair KPIs, built from real database records.

**Where to find it:** Sidebar → **📈 Advanced Analytics**.

**Test steps:**
1. Click **📈 Advanced Analytics** in the sidebar.
2. Review the charts: detection trends, severity distribution, area-wise bar chart, and repair KPI charts.
3. Hover over any chart bar or segment to see the interactive tooltip.

**Expected result:** All charts render without errors. Hovering over a chart element shows a popup with the exact count or value. If the database is empty, placeholder messages appear.

---

### Feature 15 — Simulation Lab

**Purpose:** Generates realistic hypothetical scenarios for planning and decision-making. All simulated data is strictly isolated from real records.

**Where to find it:** Sidebar → **🔬 Simulation Lab**.

**Test steps:**
1. Click **🔬 Simulation Lab** in the sidebar.
2. Note the prominent yellow warning banner: "⚠ SIMULATED DATA — Never contaminates real records."
3. In the **Configure Scenario** tab:
   - Set **Scenario Name:** `Demo Scenario A`
   - Set **Number of simulated potholes:** `200`
   - Set **Repair strategy:** `Priority (Highest Severity First)`
   - Set **Budget:** `₹1,000,000`
4. Click **▶️ Run Simulation**.
5. A success message appears. Switch to the **Scenario Results** tab.

**Expected result:** KPI tiles show simulated totals (e.g., 200 potholes, repaired count, budget used). Charts labelled **[SIMULATED]** appear, including a severity donut chart, repair status bar chart, and area-wise breakdown.

6. Go back to **Configure Scenario**, change the scenario name to `Demo Scenario B`, change the budget to `₹500,000`, and click **💾 Run & Save Scenario**.
7. Switch to **Compare Scenarios** tab. Both saved scenarios appear in dropdowns; a grouped bar chart compares them side by side.

**Common problems:**
- "Save at least 2 scenarios to compare them here": Run and save two scenarios before switching to the Compare tab.

---

### Feature 16 — Model Performance Page

**Purpose:** Displays verified evaluation metrics from the actual YOLO11n model testing. No numbers are fabricated.

**Where to find it:** Sidebar → **🏆 Model Performance**.

**Test steps:**
1. Click **🏆 Model Performance** in the sidebar.
2. Review the primary model KPI grid (Precision, Recall, F1, mAP@50, mAP@50-95, Inference Time).
3. Scroll to the **Model Comparison** section. A data table and radar chart compare YOLO11n against YOLOv8n and DETR-R50.
4. Scroll further to see **Dataset Statistics** and the **Operational Inference Statistics** from the live database.

**Expected result:**
- KPI tiles show real metrics: mAP@50 ≈ 78%, Precision and Recall values, and inference speed.
- The radar chart overlays all three models.
- An information box clearly states that these are test-set evaluation results, not simulated numbers.

**Key metrics to note (for the evaluator):**

| Metric | YOLO11n (Our Model) |
|--------|-------------------|
| mAP@50 (test set) | ~78.05% |
| mAP@50 (validation set) | 86.97% |
| mAP@50-95 (test set) | ~49.31% |
| Training images | 532 |
| Test images | 67 |

---

### Feature 17 — Reports and Export

**Purpose:** Generates downloadable reports in CSV, Excel, JSON, and GeoJSON formats from real database records.

**Where to find it:** Sidebar → **📤 Reports & Export**.

**Test steps:**
1. Click **📤 Reports & Export** in the sidebar.
2. Set the date range filters at the top (leave at default for a full export).
3. Click the **🔍 Detection Summary** tab. A table appears; click **⬇️ Download CSV** and verify the file opens in Excel.
4. Click the **🔧 Repair Progress** tab and click **⬇️ Repair Tasks Excel** to download an Excel file.
5. Click the **📦 Full Export** tab and click **⬇️ Download Full Excel Export**. The file is a multi-sheet Excel workbook.

**Expected result:** Each download button produces the corresponding file. The CSV files open in Excel with proper columns and data. The Full Export Excel contains separate sheets for Detections, Repair Tasks, Locations, KPI Summary, and Export Metadata.

---

## 5. Quick Demo Flow (5 Minutes)

The following is a suggested route to demonstrate the most important features in the shortest time. Follow the steps in this order.

| Step | Action | Time |
|------|---------|------|
| 1 | Open **https://roadsight.streamlit.app/** in Chrome. If the app is sleeping, click "Wake up" and wait. Point to the Home page metric tiles and feature cards. | 0:30 |
| 2 | Click **🔍 Live Detection** → **Demo Samples** tab. Select a sample image and click **▶ Run Demo Inference**. Show the side-by-side detection result and the detection table. | 1:00 |
| 3 | Click the **Image Detection** tab. Upload a real road photograph. Lower the confidence slider to 0.30 and observe the result. Download the CSV. | 1:00 |
| 4 | Click **🗺️ GIS Map**. If markers exist, show the map with popup. Otherwise, click Add Location, type a city name and coordinates, and save. Return to Map View to show the new marker. | 0:45 |
| 5 | Click **🔧 Repair Management**. Create a quick repair task (select any detection, set priority to High, click Create). Then open Task Detail, change status to "In Progress", and save. Show the status timeline. | 1:00 |
| 6 | Click **📊 Executive Overview**. Show the KPI tiles, timeline chart, and severity donut chart updating with the data just entered. | 0:30 |
| 7 | Click **🏆 Model Performance**. Show the mAP@50 metric and the radar chart comparing three models. | 0:15 |

**Total: approximately 5 minutes**

---

## 6. Technology and Structure

### Frontend

The entire user interface is built with **Streamlit** (Python), a rapid development framework that turns Python scripts into interactive web applications. Each page in the application is a separate Python file in the `pages/` folder. Charts are rendered using the **Plotly** library for interactive, responsive visualisations.

### Backend and AI Model

The AI detection model is **YOLO11n** (You Only Look Once, version 11, Nano), provided by the **Ultralytics** library. The model was custom-trained on a dataset of 665 annotated road images using Google Colab. The model weight file is stored at `models/best.pt`. All inference runs locally on the host computer; no images or data are ever sent to an external server.

The geographic map is rendered using the **Folium** library with free **OpenStreetMap** tiles. Address geocoding uses **Nominatim** (also from OpenStreetMap), which requires an internet connection.

### Database

All detection records, location pins, repair tasks, and simulation scenarios are stored in a single **SQLite** database file located at `data/roadintel.db`. SQLite is a lightweight, file-based relational database that requires no separate server. The simulation data is stored in completely separate tables (`simulation_runs`, `simulation_records`) and never appears in the real operational views.

### Hosting

The application is deployed publicly on **Streamlit Community Cloud** and is accessible at **https://roadsight.streamlit.app/** — no installation is required for evaluation. The source code and model weights are stored on **GitHub**, and Streamlit Cloud builds and serves the app directly from that repository. A local installation option is also available as a fallback (see Section 2, Option B).

---

## 7. Limitations and Future Improvements

### Current Limitations

| Limitation | Explanation |
|---|---|
| Single detection class | The model detects only potholes (`pothole`, class ID 0). It cannot classify road cracks, markings, or other defects. |
| No depth estimation | Pothole depth cannot be determined from a 2D photograph. Severity (Low/Medium/High/Critical) is estimated from the bounding box size relative to the image, not the actual physical depth. |
| GPS depends on user input | The application has no GPS receiver. All map coordinates must be entered manually, typed as an address for geocoding, or selected by clicking the map. |
| Small training dataset | The model was trained on 665 images. Performance on unusual road types, low-light conditions, or extreme camera angles may be reduced. |
| Local-only deployment | The application runs on a single computer. It is not accessible from other devices on a network without additional configuration. |
| No user authentication | There are no user accounts or role-based access controls in the current version. |

### Planned Future Improvements

- **Instance segmentation:** Train a YOLO11n-Seg model to outline the exact shape of each pothole, rather than a rectangular bounding box.
- **Larger, more diverse dataset:** Collect road images from multiple cities and lighting conditions to improve real-world generalisation.
- **Mobile application:** Build a companion mobile app that captures and submits road photographs with automatic GPS tagging.
- **Real-time camera stream processing:** Support live CCTV or dashcam video streams instead of uploaded files only.
- **Role-based access:** Add a login system with separate roles for field workers, supervisors, and administrators.
- **Cloud deployment:** Host the platform on a cloud server so multiple users can access it simultaneously.
- **Automated report scheduling:** Allow the system to email weekly PDF summaries to road authority email addresses.

---

## 8. Contact

For any questions about this project, please raise them directly during the evaluation session or send a written query through the college's official channel.

> **Subject Line to use:** RoadSight Platform — Evaluation Query

---

*This guide was prepared for academic evaluation of the RoadSight Intelligence Platform v2.0.*
*All metrics and features described in this document reflect the actual implementation.*
*No results have been fabricated or estimated without a real technical basis.*
