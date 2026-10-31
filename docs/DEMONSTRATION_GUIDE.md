# Demonstration Guide

A concise script for presenting this project at a college submission demo.

---

## Setup (before the demo)

```powershell
cd pothole-detection-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The browser opens at `http://localhost:8501`.

---

## Demo Sequence (approx. 10 minutes)

### Step 1 — Overview tab (1 min)
- Show the hero banner and explain the project.
- Point out the **Model loaded ✓** indicator in the sidebar.
- Briefly describe the dataset (665 images, one class: pothole).

### Step 2 — Image Detection tab (3 min)
- Upload one of the sample images from `assets/sample_images/`.
  (Or expand the "Run demo on a sample image" panel — no upload needed.)
- Show the **original** and **annotated** images side by side.
- Point out the bounding boxes, class label (`pothole`), and confidence score.
- Show the detection table below the images.
- Download the annotated PNG and the CSV — open them to confirm real output.

### Step 3 — Model Evaluation tab (3 min)
- Open the **metric definitions** expander and briefly explain Precision/Recall/mAP.
- Show the **test-split model comparison table** and highlight YOLO11n as rank 1.
- Show the **training audit table** and explain that YOLO11n_800 achieved the highest
  validation mAP@50 (86.97%).
- Point out the "Metrics not available" table — demonstrates honest reporting.

### Step 4 — About Research tab (2 min)
- Show the research status checklist.
- Explain the segmentation pilot badge: manual annotations exist, but no trained
  segmentation model yet.
- Briefly outline future work.

---

## Answers to Likely Questions

**Q: What is mAP@50?**
Mean Average Precision at 0.50 IoU.  A predicted box counts as correct only if it
overlaps the ground-truth box by at least 50%.  Averaged across all recall levels,
this gives a single performance figure.

**Q: Why is the test mAP lower than the validation mAP?**
The validation split was used throughout training to select the best checkpoint,
so it is not independent.  The test split (held out completely) gives a more
honest estimate of generalisation.

**Q: Can you detect depth or severity?**
No.  Physical depth cannot be determined from a single monocular RGB image.  The app
displays bounding-box area as an experimental proxy only.

**Q: Is this deployed online?**
No.  This is a local prototype.  The app runs entirely on the local machine without
internet access after installation.

**Q: What about video?**
The Video Detection tab supports MP4 and AVI uploads.  Processing is CPU-bound and
takes a few minutes for a short clip.  The annotated output video can be downloaded.
