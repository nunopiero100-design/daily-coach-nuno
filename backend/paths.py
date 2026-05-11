import os
from pathlib import Path


def get_data_dir() -> Path:
    return Path(os.getenv("DATA_DIR", "data")).resolve()


def get_reports_dir() -> Path:
    return get_data_dir() / "reports"


def get_feedback_dir() -> Path:
    return get_data_dir() / "feedback"