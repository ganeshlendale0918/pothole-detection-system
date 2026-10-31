# Testing Documentation

## Test Environment
- **Framework:** pytest (v8.0+)
- **Location:** `tests/`
- **Virtual environment:** `.venv/`

## Running Tests

```powershell
cd d:\Coding\A-PROJECTS\Pothole_Submission\pothole-detection-system
.venv\Scripts\pytest tests\ -v
```

## Syntax Validation (All Pages)

```powershell
foreach ($f in Get-ChildItem pages\*.py) {
    .venv\Scripts\python.exe -m py_compile $f.FullName
    Write-Host "$($f.Name): $(if ($LASTEXITCODE -eq 0) { 'OK' } else { 'FAIL' })"
}
.venv\Scripts\python.exe -m py_compile app.py
```

## Module Import Verification

```powershell
.venv\Scripts\python.exe -c "
import sys; sys.path.insert(0,'.')
import config
from src.database import init_db; init_db(); print('DB OK')
from src.ui_components import inject_css; print('UI OK')
from src.model_loader import load_model_metadata, get_model_info; print('Loader OK')
from src.severity import classify_severity; print('Severity OK')
from src.risk_score import compute_area_risk_scores; print('Risk OK')
from src.reporting import detections_to_csv_bytes; print('Reporting OK')
"
```

## Upgrade Verification Results

| Check | Result |
|-------|--------|
| `app.py` syntax | ✅ OK |
| `pages/1_Executive_Overview.py` syntax | ✅ OK |
| `pages/2_Live_Detection.py` syntax | ✅ OK |
| `pages/3_Detection_History.py` syntax | ✅ OK |
| `pages/4_GIS_Map.py` syntax | ✅ OK |
| `pages/5_Road_Condition_Intelligence.py` syntax | ✅ OK |
| `pages/6_Repair_Management.py` syntax | ✅ OK |
| `pages/7_Advanced_Analytics.py` syntax | ✅ OK |
| `pages/8_Simulation_Lab.py` syntax | ✅ OK |
| `pages/9_Model_Performance.py` syntax | ✅ OK |
| `pages/10_Reports_Export.py` syntax | ✅ OK |
| `pages/11_Settings.py` syntax | ✅ OK |
| `src/database.py` import | ✅ DB initialised |
| `src/ui_components.py` import | ✅ OK |
| `src/model_loader.py` import + metadata | ✅ YOLO11n metadata loaded |
| `config.py` import | ✅ OK |
| `models/best.pt` present | ✅ 5.25 MB |
| `models/model_metadata.json` present | ✅ OK |
| `research_reports/results/final_model_comparison.json` | ✅ OK |
| `research_reports/results/final_model_comparison.csv` | ✅ OK |

## Test Cases (Manual Verification)

### Live Detection
1. Upload a test image from `assets/sample_images/`
2. Run detection at default conf=0.45
3. Verify bounding boxes and severity labels appear
4. Click "Save Detection" → verify record appears in Detection History
5. Download CSV → verify fields populated

### Detection History
1. Navigate to Detection History
2. Filter by severity "High" → verify only High records shown
3. Search by filename → verify filter works
4. Download filtered CSV

### GIS Map
1. Navigate to GIS Map
2. Enter a valid address → geocode → verify marker appears
3. Enter manual lat/lon → save → verify different marker colour in list
4. Filter by severity → verify only matching markers shown

### Repair Management
1. Create a task linked to a saved detection
2. Task verifies at status "Pending Verification"
3. Navigate to Task Detail, update to "Verified"
4. Verify status log shows the transition
5. Update to "In Progress" → "Repaired" → "Closed"
6. Restart app → verify task still shows "Closed"

### Simulation Lab
1. Configure: 100 potholes, 30% Critical, Priority strategy, ₹100,000 budget
2. Run Simulation
3. Verify results show in Scenario Results tab
4. Verify KPIs match configuration expectations
5. Save scenario → verify appears in Saved Scenarios
6. Run second scenario → compare both in Compare tab
7. Verify NO simulated records appear in Executive Overview or Detection History

### Model Performance
1. Navigate to Model Performance
2. Verify YOLO11n KPI strip shows values from final_model_comparison.json
3. Verify comparison table matches CSV
4. Verify dataset stats match config.py constants

### Reports & Export
1. Go to Reports & Export with default date range
2. Detection Summary: verify count matches Detection History
3. Severity Report: verify breakdown
4. Location Report: download GeoJSON, verify valid JSON
5. Full Export: download Excel → open → verify multiple sheets

### Settings
1. Change default confidence to 0.55 → save
2. Navigate to Live Detection → verify slider default is now 0.55
3. Change map default lat → save → navigate to GIS Map → verify centre changed

## Known Test Limitations
- Webcam input cannot be automated tested in current environment
- Video processing tests require sample video files
- Geocoding tests require internet connectivity
- PDF generation tests require fpdf2 to be installed
