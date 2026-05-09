from datetime import date, datetime

from backend.schemas import DailyCoachReport, Recommendation


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
        recommendation=Recommendation(
            action="KEEP",
            headline="Mantém o treino",
            details="Sono, HRV e resting HR estão aceitáveis. Não há razão para cortar carga hoje.",
        ),
    )

    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
