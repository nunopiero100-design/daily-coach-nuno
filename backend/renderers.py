from backend.schemas import DailyCoachReport


def _fmt(value, suffix: str = "") -> str:
    if value is None:
        return "—"
    return f"{value}{suffix}"


def render_daily_email(report: DailyCoachReport) -> str:
    lines: list[str] = []

    lines.append(f"Daily Coach — {report.date.isoformat()}")
    lines.append("")
    lines.append(f"Estado: {report.status}")
    lines.append(f"Título: {report.title}")
    lines.append("")
    lines.append(report.summary)
    lines.append("")

    if report.flags.incomplete_essential_data:
        lines.append("⚠️ Dados incompletos")
        lines.append(
            "Dados incompletos, atualiza/sincroniza no Intervals e corre manualmente."
        )
        lines.append("")

    lines.append("Recomendação")
    lines.append("------------")
    lines.append(f"Ação: {report.recommendation.action}")
    lines.append(f"{report.recommendation.headline}")
    lines.append(report.recommendation.details)
    lines.append("")

    if report.recommendation.workout_modification:
        lines.append("Ajuste ao treino")
        lines.append("----------------")
        lines.append(report.recommendation.workout_modification)
        lines.append("")

    if report.recommendation.indoor_alternative:
        lines.append("Alternativa indoor")
        lines.append("------------------")
        lines.append(report.recommendation.indoor_alternative)
        lines.append("")

    lines.append("Treino planeado")
    lines.append("---------------")
    lines.append(f"Nome: {_fmt(report.planned_workout.name)}")
    lines.append(f"Duração: {_fmt(report.planned_workout.duration_minutes, ' min')}")
    lines.append(f"TSS planeado: {_fmt(report.planned_workout.planned_tss)}")
    lines.append(f"Fonte: {_fmt(report.planned_workout.source or report.source_plan)}")
    if report.planned_workout.description:
        lines.append("")
        lines.append(report.planned_workout.description)
    lines.append("")

    lines.append("Atividade feita hoje")
    lines.append("--------------------")
    if report.completed_activity.exists:
        lines.append(f"Nome: {_fmt(report.completed_activity.name)}")
        lines.append(f"Duração: {_fmt(report.completed_activity.duration_minutes, ' min')}")
        lines.append(f"TSS: {_fmt(report.completed_activity.tss)}")
        lines.append(f"NP: {_fmt(report.completed_activity.normalized_power, ' W')}")
        lines.append(f"IF: {_fmt(report.completed_activity.intensity_factor)}")
    else:
        lines.append("Ainda não há atividade registada hoje.")
    lines.append("")

    lines.append("Recuperação")
    lines.append("-----------")
    lines.append(f"Sono: {_fmt(report.readiness.sleep_hours, ' h')}")
    lines.append(f"HRV: {_fmt(report.readiness.hrv)}")
    lines.append(f"Resting HR: {_fmt(report.readiness.resting_hr, ' bpm')}")
    lines.append(f"Fitness/CTL: {_fmt(report.readiness.fitness_ctl)}")
    lines.append(f"Fatigue/ATL: {_fmt(report.readiness.fatigue_atl)}")
    lines.append(f"Form: {_fmt(report.readiness.form)}")
    if report.readiness.notes:
        lines.append(f"Notas: {report.readiness.notes}")
    lines.append("")

    lines.append("Peso & fueling")
    lines.append("--------------")
    lines.append(f"Peso atual: {_fmt(report.weight.current_kg, ' kg')}")
    lines.append(f"Média 7 dias: {_fmt(report.weight.avg_7d_kg, ' kg')}")
    lines.append(f"Objetivo: {_fmt(report.weight.target_kg, ' kg')}")
    lines.append(f"Tendência semanal: {_fmt(report.weight.weekly_trend_kg, ' kg/semana')}")
    lines.append(f"Proteína: {report.fueling.protein_target_g}")

    if report.weight.guidance:
        lines.append(report.weight.guidance)
    if report.fueling.carb_guidance:
        lines.append(report.fueling.carb_guidance)
    if report.fueling.deficit_guidance:
        lines.append(report.fueling.deficit_guidance)
    if report.fueling.notes:
        lines.append(report.fueling.notes)

    lines.append("")
    lines.append("Texto completo")
    lines.append("--------------")
    lines.append(report.full_text)
    lines.append("")
    lines.append(f"Auto-apply: {report.auto_apply}")

    return "\n".join(lines)