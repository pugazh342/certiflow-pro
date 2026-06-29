# config.py
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"
PDF_OUTPUT_DIR = WORKSPACE_DIR / "generated_pdfs"
CHECKPOINT_DIR = WORKSPACE_DIR / "checkpoints"
AUDIT_DIR = WORKSPACE_DIR / "audit_logs"
TEMPLATE_DIR = BASE_DIR / "templates"

# File Locations
CHECKPOINT_FILE = CHECKPOINT_DIR / "current_job.json"
BASE_CERT_TEMPLATE = TEMPLATE_DIR / "base_cert.html"

# SMTP Defaults
DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587

# Rate Limiting (Jitter Seconds)
JITTER_MIN = 1.5
JITTER_MAX = 3.2

# PDF Layout Engine
MAX_NAME_LEN_NORMAL_FONT = 22
NORMAL_FONT_SIZE_PX = 54
SCALED_FONT_SIZE_PX = 36

def initialize_directories() -> None:
    """Ensures the runtime workspace structure exists securely."""
    for directory in [PDF_OUTPUT_DIR, CHECKPOINT_DIR, AUDIT_DIR, TEMPLATE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

initialize_directories()