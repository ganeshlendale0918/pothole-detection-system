# AI-Based Road Pothole Detection System

> A custom-trained YOLO11n object-detection application for road surface analysis,
> built as a college academic project.

---

## Overview

This project trains and deploys a single-class (`pothole`) YOLO11n object-detector
on a custom annotated dataset of 665 road images.  The Streamlit application loads
the trained checkpoint locally and supports:

- **Image detection** — upload a road photo, get bounding boxes + CSV/JSON download
- **Video detection** — frame-by-frame inference with annotated video output
- **Research dashboard** — verified evaluation metrics, training audit, model comparison
- **Transparent limitations** — clearly distinguishes validation from test performance

---

## Features

| Feature | Description |
|---|---|
| Image upload & inference | JPG, PNG, WEBP |
| Video upload & inference | MP4, AVI (OpenCV-supported codecs) |
| Adjustable thresholds | Confidence, IoU, image size |
| Annotated downloads | PNG image, MP4 video |
| CSV export | Per-detection structured report |
| JSON summary | Structured metadata per run |
| Research metrics | Verified from actual experiment reports |
| Demo mode | Run on bundled sample images without uploading |

---

## Architecture

```
pothole-detection-system/
├── app.py                  ← Streamlit UI (all 6 tabs)
├── config.py               ← Paths, defaults, constants
├── requirements.txt
├── .gitignore
│
├── models/
│   ├── best.pt             ← Custom YOLO11n checkpoint (required)
│   └── model_metadata.json ← Inference defaults and model info
│
├── src/
│   ├── __init__.py
│   ├── model_loader.py     ← Cached YOLO model loading
│   ├── image_inference.py  ← Still-image inference pipeline
│   ├── video_inference.py  ← Frame-by-frame video pipeline
│   ├── reporting.py        ← CSV/JSON export utilities
│   └── validation.py       ← Input validation helpers
│
├── assets/
│   └── sample_images/      ← Bundled demo images
│
├── outputs/                ← Generated files (excluded from git)
│
├── research_reports/
│   └── results/            ← Verified experiment CSVs/JSONs
│
├── tests/
│   ├── test_validation.py
│   └── test_reporting.py
│
└── docs/
    ├── PROJECT_REPORT.md
    ├── METHODOLOGY.md
    └── RESULTS_AND_LIMITATIONS.md
```

---

## Dataset Summary

| Property | Value |
|---|---|
| Total images | 665 |
| Training split | 532 |
| Validation split | 66 |
| Test split | 67 |
| Annotation format | Pascal VOC XML → YOLO |
| Detection classes | `pothole` (class ID 0) |

---

## Model Checkpoint

| Property | Value |
|---|---|
| Architecture | YOLO11n (Ultralytics) |
| Training | Google Colab, pretrained on COCO |
| Inference image size | 800 px |
| Default confidence | 0.45 |
| Default IoU/NMS | 0.45 |
| Checkpoint file | `models/best.pt` |

**Validation metrics (validation split, from training audit):**
- mAP@50: **86.97%**
- mAP@50-95: **58.67%**

> ⚠️ These are validation-split figures, not independent test-set performance.
> Test-split metrics (640 px model): mAP@50 78.05%, mAP@50-95 49.31%.

---

## Installation (Windows PowerShell)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Upgrade pip
python -m pip install --upgrade pip

# 3. Install dependencies
pip install -r requirements.txt
```

### If PowerShell execution policy blocks activation

```powershell
# Option A — run for this session only (no system change)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1

# Option B — use the venv Python directly without activating
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

---

## Starting the Application

```powershell
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

---

## Usage

1. **Overview tab** — project summary, dataset info, sample gallery
2. **Image Detection tab** — upload a road image → inference runs automatically
3. **Video Detection tab** — upload a video → set frame limit → click "Process"
4. **Results & Exports tab** — download verified research report CSVs
5. **Model Evaluation tab** — view test-split and validation metrics with definitions
6. **About Research tab** — project background, limitations, future scope

---

## Supported Inputs and Outputs

| Type | Input formats | Output |
|---|---|---|
| Image | `.jpg`, `.jpeg`, `.png`, `.webp` | Annotated PNG + CSV + JSON |
| Video | `.mp4`, `.avi`, `.mov` | Annotated MP4 + CSV + JSON |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Model checkpoint not found` | Ensure `models/best.pt` exists |
| `Ultralytics is not installed` | Run `pip install ultralytics` |
| Activation blocked by PowerShell policy | See "If PowerShell execution policy blocks activation" above |
| Video codec error | Convert video to MP4 H.264 with ffmpeg or VLC |
| Very slow video processing | Reduce the frame limit slider in the Video Detection tab |
| `ModuleNotFoundError: cv2` | Run `pip install opencv-python-headless` |

---

## Limitations

- Only one class (`pothole`) is detected.
- Physical depth/severity cannot be determined from RGB alone.
- GPS coordinates are not available unless user-provided.
- The dataset is small (665 images); performance on unseen road types may vary.
- The app does not have a trained segmentation model.

---

## Research Status

| Component | Status |
|---|---|
| Dataset annotation | ✅ Complete |
| YOLO training | ✅ Complete |
| Model comparison | ✅ Complete |
| Streamlit app | ✅ Complete |
| Segmentation pilot | 🔬 In progress (annotation only) |
| Full segmentation training | 🔲 Future work |

---

## Running Tests

```powershell
pytest tests/ -v
```

All tests cover: file-extension validation, model-path validation, detection-record
schema, CSV generation, JSON summary, and filename sanitisation.

---

## Future Work

- Instance segmentation (YOLO11n-Seg)
- Larger and more geographically diverse dataset
- GPS metadata integration for road mapping
- Mobile / edge device optimisation
- Severity estimation heuristics
