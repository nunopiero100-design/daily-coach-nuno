from pathlib import Path

from backend.db import is_postgres_configured
from backend.paths import get_reports_dir
from backend.schemas import DailyCoachReport


DEFAULT_REPORTS_DIR = get_reports_dir()


def save_daily_report(
    report: DailyCoachReport,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> Path:
    if is_postgres_configured():
        from backend.postgres_storage import save_daily_report_db
        return save_daily_report_db(report)

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    output_path = reports_path / f"{report.date.isoformat()}.json"

    output_path.write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8",
    )

    return output_path


def load_daily_report(
    report_date: str,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> dict:
    if is_postgres_configured():
        from backend.postgres_storage import load_daily_report_db
        return load_daily_report_db(report_date)

    reports_path = Path(reports_dir)
    input_path = reports_path / f"{report_date}.json"

    if not input_path.exists():
        raise FileNotFoundError(f"Report not found: {input_path}")

    import json

    return json.loads(input_path.read_text(encoding="utf-8"))


def list_daily_reports(
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> list[Path]:
    if is_postgres_configured():
        from backend.postgres_storage import list_daily_reports_db
        return list_daily_reports_db()

    reports_path = Path(reports_dir)

    if not reports_path.exists():
        return []

    return sorted(reports_path.glob("*.json"), reverse=True)