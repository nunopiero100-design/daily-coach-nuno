import datetime as dt
import os
import time
from pathlib import Path

import requests
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.apply import ApplyError, apply_for_today, preview_apply_for_today
from backend.auth import require_app_token, require_ingest_token
from backend.schemas import DailyCoachReport
from backend.feedback import (
    FeedbackEntry,
    list_feedback,
    load_feedback_for_date,
    save_feedback,
)
from backend.storage import DEFAULT_REPORTS_DIR, list_daily_reports, load_daily_report, save_daily_report


app = FastAPI(
    title="Daily Coach API",
    version="0.1.0",
    description="API local para servir relatórios estruturados do Daily Coach.",
)

# Without this, the mobile app's WebView (a different origin from this API)
# gets its requests silently blocked by the browser's CORS policy - the HTTP
# call can even succeed server-side, but the app never gets to read the
# response. allow_origins=["*"] is fine here: every route (except /health)
# is still gated by a Bearer token, so an open CORS policy doesn't expose
# anything - it just stops the browser from blocking legitimate calls.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackRequest(BaseModel):
    date: dt.date
    type: str
    note: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "daily-coach-api",
    }


@app.get("/api/v1/reports")
def get_reports(
    limit: int = Query(default=30, ge=1, le=365),
    _: None = Depends(require_app_token),
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
def get_today_report(
    _: None = Depends(require_app_token),
):
    today = dt.date.today().isoformat()

    try:
        return load_daily_report(today, DEFAULT_REPORTS_DIR)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for today: {today}",
        )


# In-memory cooldown so a double-tap (or an accidental repeat) doesn't fire
# the workflow twice in a row. Resets on redeploy/restart - fine for a
# personal, low-frequency button; not meant to be a hard security control.
_run_now_state = {"last_triggered_at": 0.0}
RUN_NOW_COOLDOWN_SECONDS = 180

GITHUB_OWNER = "nunopiero100-design"
GITHUB_REPO = "daily-coach-nuno"
GITHUB_WORKFLOW_FILE = "daily_coach.yml"


@app.post("/api/v1/reports/run-now")
def run_daily_coach_now(
    _: None = Depends(require_app_token),
):
    """
    Triggers the SAME GitHub Actions workflow that runs every morning,
    on demand - rather than re-implementing daily_coach_agent.py's logic
    (Intervals pull + OpenAI reasoning + ingest) a second time inside this
    API process, which would need its own copies of INTERVALS_API_KEY,
    OPENAI_API_KEY etc. and would duplicate an already-proven pipeline.

    The workflow run itself still pushes its result to /reports/ingest
    when it finishes (typically ~30-90s later), same as every scheduled
    run - so the app should poll/refresh shortly after calling this,
    not expect the fresh report immediately in this response.
    """
    now = time.time()
    elapsed = now - _run_now_state["last_triggered_at"]
    if elapsed < RUN_NOW_COOLDOWN_SECONDS:
        wait = int(RUN_NOW_COOLDOWN_SECONDS - elapsed)
        raise HTTPException(
            status_code=429,
            detail=f"Já foi pedida uma atualização há pouco. Tenta novamente em ~{wait}s.",
        )

    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not github_token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN não configurado no backend.")

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW_FILE}/dispatches"
    try:
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"ref": "main"},
            timeout=20,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro a contactar o GitHub: {e}")

    if r.status_code != 204:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub recusou o pedido: HTTP {r.status_code} {r.text[:200]}",
        )

    _run_now_state["last_triggered_at"] = now
    return {
        "status": "triggered",
        "message": "Pedido enviado. Demora tipicamente ~30-90s a aparecer no relatório - atualiza daqui a pouco.",
    }


@app.post("/api/v1/reports/ingest")
def ingest_report(
    report: DailyCoachReport,
    _: None = Depends(require_ingest_token),
):
    """
    Called by daily_coach_agent.py (GitHub Actions) right after it builds
    today's structured report - this is what makes GET /reports/today
    actually have fresh data, instead of the two being disconnected islands.
    Protected by INGEST_TOKEN, not APP_TOKEN - see auth.py for why.
    """
    saved_path = save_daily_report(report)
    return {"status": "saved", "date": report.date.isoformat(), "path": str(saved_path)}


@app.get("/api/v1/reports/today/apply/preview")
def get_apply_preview(
    _: None = Depends(require_app_token),
):
    """
    Shows what the 'Apply reduced workout' button WOULD do, without writing
    anything to Intervals.icu. The app should always call this first and let
    the person confirm before calling the POST endpoint below.
    """
    try:
        return preview_apply_for_today()
    except ApplyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Sem relatório para hoje.")


@app.post("/api/v1/reports/today/apply")
def post_apply_today(
    _: None = Depends(require_app_token),
):
    """
    Actually replaces today's planned workout on Intervals.icu with the
    reduced/recovery version. Only valid when today's status is YELLOW or RED.
    """
    try:
        return apply_for_today()
    except ApplyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Sem relatório para hoje.")


@app.get("/api/v1/reports/{report_date}")
def get_report_by_date(
    report_date: str,
    _: None = Depends(require_app_token),
):
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

@app.post("/api/v1/feedback")
def create_feedback(
    payload: FeedbackRequest,
    _: None = Depends(require_app_token),
):
    feedback = FeedbackEntry(
        date=payload.date,
        type=payload.type,
        note=payload.note,
    )

    saved_path = save_feedback(feedback)

    return {
        "status": "saved",
        "path": str(saved_path),
        "feedback": json_safe_feedback(feedback),
    }


@app.get("/api/v1/feedback")
def get_feedback(
    date: str | None = None,
    _: None = Depends(require_app_token),
):
    if date:
        try:
            dt.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD.",
            )

        return {
            "count": len(load_feedback_for_date(date)),
            "feedback": load_feedback_for_date(date),
        }

    feedback = list_feedback()

    return {
        "count": len(feedback),
        "feedback": feedback,
    }


def json_safe_feedback(feedback: FeedbackEntry) -> dict:
    return {
        "date": feedback.date.isoformat(),
        "type": feedback.type,
        "note": feedback.note,
        "created_at": feedback.created_at.isoformat(),
    }