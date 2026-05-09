from datetime import date, datetime

from backend.renderers import render_daily_email
from backend.schemas import (
    DailyCoachReport,
    FuelingAdvice,
    PlannedWorkout,
    ReadinessData,
    Recommendation,
    WeightData,
)


def main():
    report = DailyCoachReport(
        date=date.today(),
        generated_at=datetime.now(),
        status="GREEN",
        title="Mantém o treino planeado",
        summary="Dados de recuperação bons. Mantém o treino FasCat previsto.",
        full_text=(
            "Hoje estás em condições de manter o treino planeado. "
            "Alimenta bem o treino e evita défice agressivo."
        ),
        planned_workout=PlannedWorkout(
            name="Sweet Spot / Tempo",
            description="Treino FasCat principal do dia.",
            duration_minutes=90,
            planned_tss=85,
            source="FasCat",
        ),
        readiness=ReadinessData(
            sleep_available=True,
            hrv_available=True,
            resting_hr_available=True,
            sleep_hours=7.4,
            hrv=58,
            resting_hr=43,
            fitness_ctl=72,
            fatigue_atl=81,
            form=-9,
        ),
        weight=WeightData(
            current_kg=77.0,
            avg_7d_kg=76.8,
            target_kg=74.0,
            weekly_trend_kg=-0.3,
            guidance="Tendência dentro do alvo. Não apertar mais a dieta.",
        ),
        fueling=FuelingAdvice(
            carb_guidance="Dia com intensidade: alimenta o treino antes e durante.",
            deficit_guidance="Evita défice agressivo hoje.",
        ),
        recommendation=Recommendation(
            action="KEEP",
            headline="Mantém o treino",
            details="Sono, HRV e resting HR estão aceitáveis. Não há razão para cortar carga hoje.",
        ),
    )

    print(render_daily_email(report))


if __name__ == "__main__":
    main()