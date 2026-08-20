"""
Apply-to-Intervals logic for the "Apply reduced workout" app button.

Reuses the existing replacement-building logic from daily_coach_agent.py
instead of duplicating it - build_replacement_event(), choose_replacement_kind(),
replacement_steps() and IntervalsClient all already exist and are proven; this
module just wires them up to the API.

Design choice: today's ORIGINAL planned event is re-fetched live from
Intervals.icu rather than trusted from the stored structured report, because
PlannedWorkout (schemas.py) doesn't carry external_id / start_date_local / type
- and build_replacement_event() refuses to run without a real external_id
(to avoid creating a duplicate event instead of replacing the right one).
Re-fetching fresh also guarantees we're never modifying a stale morning
snapshot.
"""
import os
import datetime as dt

import daily_coach_agent as dca
from backend.storage import DEFAULT_REPORTS_DIR, load_daily_report


STATUS_TO_PT = {
    "GREEN": "VERDE",
    "YELLOW": "AMARELO",
    "RED": "VERMELHO",
    "INCOMPLETE": "DADOS INCOMPLETOS",
}


class ApplyError(Exception):
    """Raised for expected, user-facing failure states (not a 500)."""


def _client_from_env():
    intervals_key = os.getenv("INTERVALS_API_KEY", "").strip()
    athlete_id = os.getenv("ATHLETE_ID", "0").strip() or "0"
    if not intervals_key:
        raise ApplyError("INTERVALS_API_KEY não configurado no backend (Render).")
    client = dca.IntervalsClient(athlete_id, intervals_key)
    athlete = client.athlete()
    if athlete_id == "0" and athlete.get("id"):
        client.athlete_id = athlete["id"]
    return client


def _reasons_and_actions_from_recommendation(recommendation: dict):
    """
    The structured schema flattens the old reasons/actions lists into
    recommendation.details (reasons+actions joined) and
    recommendation.workout_modification (actions only, for YELLOW/RED).
    Recover both lists by set difference rather than guessing.
    """
    details = recommendation.get("details") or ""
    workout_modification = recommendation.get("workout_modification") or ""
    actions = [l for l in workout_modification.split("\n") if l.strip()]
    all_lines = [l for l in details.split("\n") if l.strip()]
    reasons = [l for l in all_lines if l not in actions]
    if not actions:
        actions = all_lines
    return reasons, actions


def _build_replacement(target_date: dt.date):
    report = load_daily_report(target_date.isoformat(), DEFAULT_REPORTS_DIR)

    status_en = report.get("status")
    status_pt = STATUS_TO_PT.get(status_en, "DADOS INCOMPLETOS")
    if status_pt not in ("AMARELO", "VERMELHO"):
        raise ApplyError(
            f"O relatório de hoje está {status_en}; não há substituição para aplicar."
        )

    client = _client_from_env()
    today_events = client.events_range(target_date, target_date)
    workout_events = [e for e in today_events if e.get("type") or e.get("category") == "WORKOUT"]
    if not workout_events:
        raise ApplyError("Não encontrei nenhum treino planeado hoje em Intervals.icu.")

    original = workout_events[0]
    recommendation = report.get("recommendation") or {}
    reasons, actions = _reasons_and_actions_from_recommendation(recommendation)
    decision_text = recommendation.get("headline") or report.get("title") or ""

    replacement, err = dca.build_replacement_event(
        original=original,
        target_date=target_date,
        status=status_pt,
        decision_text=decision_text,
        reasons=reasons,
        actions=actions,
    )
    if err:
        raise ApplyError(err)

    return client, original, replacement


def preview_apply_for_today():
    """Builds the replacement event but does NOT write anything to Intervals."""
    _client, original, replacement = _build_replacement(dt.date.today())
    return {
        "original_name": original.get("name"),
        "new_name": replacement.get("name"),
        "new_load": replacement.get("load"),
        "duration_minutes": (replacement.get("moving_time") or 0) // 60,
        "description": replacement.get("description"),
    }


def apply_for_today():
    """Builds the replacement event AND pushes it to Intervals.icu."""
    client, original, replacement = _build_replacement(dt.date.today())
    client.upload_bulk_events([replacement])
    return {
        "applied": True,
        "original_name": original.get("name"),
        "new_name": replacement.get("name"),
        "new_load": replacement.get("load"),
    }
