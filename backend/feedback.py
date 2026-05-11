import datetime as dt
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


FeedbackType = Literal[
    "NO_TIME",
    "RAIN_INDOOR",
    "SICK",
    "INJURED",
    "NO_BIKE_WEEK",
    "MANUAL_NOTE",
]


DEFAULT_FEEDBACK_DIR = Path("data/feedback")


class FeedbackEntry(BaseModel):
    date: dt.date
    type: FeedbackType
    note: str | None = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)


def save_feedback(
    feedback: FeedbackEntry,
    feedback_dir: Path | str = DEFAULT_FEEDBACK_DIR,
) -> Path:
    feedback_path = Path(feedback_dir)
    feedback_path.mkdir(parents=True, exist_ok=True)

    output_path = feedback_path / f"{feedback.date.isoformat()}.json"

    existing = []
    if output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))

    existing.append(json.loads(feedback.model_dump_json()))

    output_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


def load_feedback_for_date(
    feedback_date: str,
    feedback_dir: Path | str = DEFAULT_FEEDBACK_DIR,
) -> list[dict]:
    feedback_path = Path(feedback_dir)
    input_path = feedback_path / f"{feedback_date}.json"

    if not input_path.exists():
        return []

    return json.loads(input_path.read_text(encoding="utf-8"))


def list_feedback(
    feedback_dir: Path | str = DEFAULT_FEEDBACK_DIR,
) -> list[dict]:
    feedback_path = Path(feedback_dir)

    if not feedback_path.exists():
        return []

    entries: list[dict] = []

    for path in sorted(feedback_path.glob("*.json"), reverse=True):
        try:
            entries.extend(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue

    return entries