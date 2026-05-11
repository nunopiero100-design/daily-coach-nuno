from pathlib import Path

from backend.schemas import DailyCoachReport


DEFAULT_REPORTS_DIR = Path("data/reports")


def save_daily_report(
    report: DailyCoachReport,
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> Path:
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
    reports_path = Path(reports_dir)
    input_path = reports_path / f"{report_date}.json"

    if not input_path.exists():
        raise FileNotFoundError(f"Report not found: {input_path}")

    import json

    return json.loads(input_path.read_text(encoding="utf-8"))


def list_daily_reports(
    reports_dir: Path | str = DEFAULT_REPORTS_DIR,
) -> list[Path]:
    reports_path = Path(reports_dir)

    if not reports_path.exists():
        return []

    return sorted(reports_path.glob("*.json"), reverse=True)