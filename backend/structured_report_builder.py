import datetime as dt

from backend.schemas import (
    CompletedActivity,
    DailyCoachReport,
    FuelingAdvice,
    PlannedWorkout,
    ReadinessData,
    Recommendation,
    ReportFlags,
    WeightData,
)


def map_status_for_structured_report(status: str | None) -> str:
    if status == "VERDE":
        return "GREEN"
    if status == "AMARELO":
        return "YELLOW"
    if status == "VERMELHO":
        return "RED"
    if status == "DADOS INCOMPLETOS":
        return "INCOMPLETE"
    if status == "JÁ FEITO":
        return "GREEN"
    return "INCOMPLETE"


def map_action_for_structured_report(status: str | None, decision: dict) -> str:
    if status == "VERDE":
        return "KEEP"
    if status == "AMARELO":
        return "REDUCE"
    if status == "VERMELHO":
        return "RECOVERY"
    if status == "DADOS INCOMPLETOS":
        return "SYNC_REQUIRED"
    if status == "JÁ FEITO":
        return "NO_TRAINING_TODAY"

    actions_text = " ".join(str(a) for a in decision.get("actions", [])).lower()

    if "descanso" in actions_text:
        return "REST"
    if "indoor" in actions_text or "rolo" in actions_text:
        return "INDOOR_ALTERNATIVE"

    return "SYNC_REQUIRED"


def find_indoor_alternative(actions: list) -> str | None:
    for action in actions:
        action_text = str(action)
        lower = action_text.lower()
        if "indoor" in lower or "rolo" in lower:
            return action_text
    return None


def build_structured_daily_report(
    target: dt.date,
    context: dict,
    decision: dict,
    report_text: str,
    auto_apply: bool,
) -> DailyCoachReport:
    today_metrics = context.get("today_metrics", {})
    baseline = context.get("baseline_14d", {})
    data_quality = context.get("data_quality", {})
    planned_events = context.get("planned_events_today", [])
    completed_today = context.get("completed_activities_today", [])
    fueling_lines = context.get("fueling_guidance", [])

    first_planned = planned_events[0] if planned_events else {}
    first_completed = completed_today[0] if completed_today else {}

    status_raw = decision.get("status")
    structured_status = map_status_for_structured_report(status_raw)
    recommendation_action = map_action_for_structured_report(status_raw, decision)

    actions = decision.get("actions", []) or []
    reasons = decision.get("reasons", []) or []

    indoor_alternative = find_indoor_alternative(actions)

    workout_modification = None
    if structured_status in ("YELLOW", "RED"):
        workout_modification = "\n".join(str(a) for a in actions)

    title = decision.get("decision_text") or {
        "GREEN": "Mantém o treino planeado",
        "YELLOW": "Reduz ou encurta o treino",
        "RED": "Recovery/Z2 ou descanso",
        "INCOMPLETE": "Dados incompletos",
    }.get(structured_status, "Daily Coach")

    summary_parts = []
    if reasons:
        summary_parts.append(str(reasons[0]))
    if actions:
        summary_parts.append(str(actions[0]))

    summary = " ".join(summary_parts) if summary_parts else title

    planned_hours = first_planned.get("hours")
    completed_hours = first_completed.get("hours")

    return DailyCoachReport(
        date=target,
        generated_at=dt.datetime.now(),
        status=structured_status,
        title=title,
        summary=summary,
        full_text=report_text,
        planned_workout=PlannedWorkout(
            name=first_planned.get("name"),
            description=None,
            duration_minutes=round(planned_hours * 60) if planned_hours is not None else None,
            planned_tss=first_planned.get("load"),
            source="FasCat",
        ),
        completed_activity=CompletedActivity(
            exists=bool(completed_today),
            name=first_completed.get("name"),
            duration_minutes=round(completed_hours * 60) if completed_hours is not None else None,
            tss=first_completed.get("load"),
        ),
        readiness=ReadinessData(
            sleep_available=today_metrics.get("sleep_hours") is not None,
            hrv_available=today_metrics.get("hrv") is not None,
            resting_hr_available=today_metrics.get("resting_hr") is not None,
            sleep_hours=today_metrics.get("sleep_hours"),
            hrv=today_metrics.get("hrv"),
            resting_hr=today_metrics.get("resting_hr"),
            fitness_ctl=today_metrics.get("fitness_ctl"),
            fatigue_atl=today_metrics.get("fatigue_atl"),
            form=today_metrics.get("form"),
            notes=None,
        ),
                weight=WeightData(
            current_kg=today_metrics.get("weight_kg"),
            avg_7d_kg=baseline.get("weight_7d"),
            target_kg=74.0,
            weekly_trend_kg=None,
            guidance=None,
        ),
        fueling=FuelingAdvice(
            protein_target_g="150–170 g/dia",
            carb_guidance=None,
            deficit_guidance=None,
            notes="\n".join(str(x) for x in fueling_lines),
        ),
        recommendation=Recommendation(
            action=recommendation_action,
            headline=title,
            details="\n".join(str(x) for x in reasons + actions),
            workout_modification=workout_modification,
            indoor_alternative=indoor_alternative,
        ),
        flags=ReportFlags(
            incomplete_essential_data=not data_quality.get("is_complete", True),
            already_trained_today=bool(completed_today),
            missed_yesterday_workout=(
                context.get("yesterday", {})
                .get("compliance", {})
                .get("status")
                == "PLANEADO MAS NÃO REALIZADO"
            ),
            weekend_indoor_option_available=context.get("calendar_context", {}).get(
                "weekend_indoor_alternative_required",
                False,
            ),
            no_bike_week=False,
            sick=False,
            injured=False,
            race_week=False,
            rain_or_indoor_constraint=False,
            no_time_constraint=False,
        ),
        source_plan="FasCat",
        auto_apply=auto_apply,
    )