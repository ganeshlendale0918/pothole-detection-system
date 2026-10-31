"""
config.py — Central configuration for the RoadSight Intelligence Platform.
All paths are relative to this file's directory so the project is portable.
"""

from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.resolve()

# ── Application metadata ──────────────────────────────────────────────────────
APP_TITLE      = "RoadSight Intelligence Platform"
APP_SUBTITLE   = "Advanced AI-Powered Road Monitoring & Analytics System"
PROJECT_VERSION = "2.0.0"

# ── Model ─────────────────────────────────────────────────────────────────────
MODELS_DIR          = ROOT_DIR / "models"
DEFAULT_MODEL_PATH  = MODELS_DIR / "best.pt"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"

# Inference defaults (from model_metadata.json)
DEFAULT_CONF   = 0.45
DEFAULT_IOU    = 0.45
DEFAULT_IMGSZ  = 800
CLASS_NAMES    = ["pothole"]

# ── Assets ────────────────────────────────────────────────────────────────────
ASSETS_DIR         = ROOT_DIR / "assets"
SAMPLE_IMAGES_DIR  = ASSETS_DIR / "sample_images"
UPLOAD_DIR         = ROOT_DIR / "data" / "uploads"
REPAIR_IMAGES_DIR  = ROOT_DIR / "data" / "repair_images"

# ── Database ──────────────────────────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data"
DB_PATH  = DATA_DIR / "roadintel.db"

# Create essential directories
for _d in (DATA_DIR, UPLOAD_DIR, REPAIR_IMAGES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Outputs ───────────────────────────────────────────────────────────────────
OUTPUTS_DIR = ROOT_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Research reports ──────────────────────────────────────────────────────────
REPORTS_DIR             = ROOT_DIR / "research_reports" / "results"
EXPERIMENT_RESULTS_CSV  = REPORTS_DIR / "experiment_results.csv"
FINAL_COMPARISON_CSV    = REPORTS_DIR / "final_model_comparison.csv"
FINAL_COMPARISON_JSON   = REPORTS_DIR / "final_model_comparison.json"
TRAINING_AUDIT_CSV      = REPORTS_DIR / "phase63_training_audit.csv"

# ── Accepted file types ───────────────────────────────────────────────────────
ACCEPTED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".webp"]
ACCEPTED_VIDEO_TYPES = [".mp4", ".avi", ".mov", ".mkv"]

# ── Dataset facts (from research audit) ──────────────────────────────────────
DATASET_TOTAL_IMAGES      = 665
DATASET_TRAIN             = 532
DATASET_VAL               = 66
DATASET_TEST              = 67
DATASET_ANNOTATION_FORMAT = "Pascal VOC XML → YOLO"
DATASET_CLASSES           = ["pothole"]

# ── Video processing limits ───────────────────────────────────────────────────
MAX_VIDEO_FRAMES     = 500
DEFAULT_VIDEO_FRAMES = 200

# ── Severity thresholds (combined score 0–1) ──────────────────────────────────
SEVERITY_THRESHOLD_CRITICAL = 0.78
SEVERITY_THRESHOLD_HIGH     = 0.58
SEVERITY_THRESHOLD_MEDIUM   = 0.38

# ── Risk score weights (must sum to 1.0) ─────────────────────────────────────
RISK_W_COUNT      = 0.30
RISK_W_SEVERITY   = 0.30
RISK_W_RECURRENCE = 0.20
RISK_W_AGE        = 0.20

# ── Repair defaults ───────────────────────────────────────────────────────────
DEFAULT_REPAIR_COST_LOW      = 500
DEFAULT_REPAIR_COST_MEDIUM   = 1500
DEFAULT_REPAIR_COST_HIGH     = 4000
DEFAULT_REPAIR_COST_CRITICAL = 10000

# ── Map defaults ──────────────────────────────────────────────────────────────
DEFAULT_MAP_LAT  = 20.5937   # India centre (neutral default)
DEFAULT_MAP_LON  = 78.9629
DEFAULT_MAP_ZOOM = 5

# ── Pagination ────────────────────────────────────────────────────────────────
PAGE_SIZE = 50
