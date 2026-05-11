import datetime as dt
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from backend.storage import DEFAULT_REPORTS_DIR, list_daily_reports, load_daily_report


app = FastAPI(
    title="Daily Coach API",
    version="0.1.0",
    description="API local para servir relatórios estruturados do Daily Coach.",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "daily-coach-api",
    }


@app.get("/api/v1/reports")
def get_reports(
    limit: int = Query(default=30, ge=1, le=365),
):
    report_paths = list_daily_reports(DEFAULT_REPORTS_DIR)[:limit]

    reports = []
    for path in report_paths:
        try:
            reports.append(load_daily_report(path.stem, DEFAULT_REPORTS_DIR))
        except Exception:
            continue

    return {
        "count": len(reports),
        "reports": reports,
    }


@app.get("/api/v1/reports/today")
def get_today_report():
    today = dt.date.today().isoformat()

    try:
        return load_daily_report(today, DEFAULT_REPORTS_DIR)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for today: {today}",
        )


@app.get("/api/v1/reports/{report_date}")
def get_report_by_date(report_date: str):
    try:
        dt.date.fromisoformat(report_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    try:
        return load_daily_report(report_date, DEFAULT_REPORTS_DIR)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for date: {report_date}",
        )