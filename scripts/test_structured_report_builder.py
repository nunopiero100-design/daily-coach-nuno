import datetime as dt

from backend.renderers import render_daily_email
from backend.structured_report_builder import build_structured_daily_report


def main():
    target = dt.date.today()

    context = {
        "today_metrics": {
            "sleep_hours": 7.4,
            "sleep_score": 82,
            "hrv": 58,
            "resting_hr": 43,
            "weight_kg": 77.0,
            "fitness_ctl": 72,
            "fatigue_atl": 81,
            "form": -9,
        },
        "baseline_14d": {
            "hrv": 56,
            "rhr": 44,
            "sleep": 7.1,
            "weight_7d": 76.8,
        },
        "planned_events_today": [
            {
                "id": "abc123",
                "external_id": "workout-001",
                "name": "FasCat Sweet Spot / Tempo",
                "load": 85,
                "hours": 1.5,
                "start_date_local": f"{target.isoformat()}T11:30:00",
                "type": "Ride",
            }
        ],
        "completed_activities_today": [],
        "yesterday": {
            "compliance": {
                "status": "CUMPRIDO",
            }
        },
        "calendar_context": {
            "weekday": target.strftime("%A"),
            "weekday_number": target.weekday(),
            "is_weekend": target.weekday() >= 5,
            "weekend_indoor_alternative_required": target.weekday() >= 5,
        },
        "data_quality": {
            "is_complete": True,
            "missing_today_metrics": [],
        },
        "fueling_guidance": [
            "Peso hoje: 77,0 kg.",
            "Média 7d: 76,8 kg.",
            "Objetivo 74 kg: faltam ~2,8 kg; apontar para 0,25–0,40 kg/semana.",
            "Proteína: 150–170 g/dia.",
            "Hoje há qualidade/intensidade: não fazer défice agressivo; alimentar bem antes e depois.",
        ],
    }

    decision = {
        "status": "VERDE",
        "decision_text": "Mantém o treino FasCat planeado.",
        "reasons": [
            "Sono, HRV e resting HR estão bons.",
            "Form está aceitável para treinar.",
            "Ontem foi cumprido sem carga excessiva.",
        ],
        "actions": [
            "Fazer o treino planeado como está.",
            "Se só tiveres 60 min: mantém o bloco principal e corta endurance final.",
            "Se for indoor/rolo: replica o treino em modo controlado.",
            "Recuperação/fueling: alimenta o treino, sem défice agressivo.",
        ],
        "should_modify_intervals": False,
        "source": "test",
    }

    report_text = "RELATÓRIO ANTIGO DE TESTE"

    structured_report = build_structured_daily_report(
        target=target,
        context=context,
        decision=decision,
        report_text=report_text,
        auto_apply=False,
    )

    print("=== JSON estruturado ===")
    print(structured_report.model_dump_json(indent=2))

    print("")
    print("=== Email renderizado ===")
    print(render_daily_email(structured_report))


if __name__ == "__main__":
    main()