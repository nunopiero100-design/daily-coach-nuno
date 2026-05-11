import datetime as dt
import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import app
from backend.schemas import DailyCoachReport, Recommendation
from backend.storage import save_daily_report


def main():
    test_reports_dir = Path("data/reports")

    test_reports_dir.mkdir(parents=True, exist_ok=True)

    today = dt.date.today()

    os.environ["APP_TOKEN"] = "test-token"

    report = DailyCoachReport(
        date=today,
        generated_at=dt.datetime.now(),
        status="GREEN",
        title="Teste API",
        summary="Relatório de teste para a API.",
        full_text="Texto completo do relatório de teste da API.",
        recommendation=Recommendation(
            action="NO_TRAINING_TODAY",
            headline="Descanso ou Z2 fácil",
            details="Teste de endpoint.",
        ),
    )

    save_daily_report(report, reports_dir=test_reports_dir)

    client = TestClient(app)
    
    headers = {"Authorization": "Bearer test-token"}
    
    health = client.get("/health")

    print("Health:", health.status_code, health.json())

    today_response = client.get("/api/v1/reports/today", headers=headers)
    print("Today:", today_response.status_code)
    print(today_response.json()["title"])

    list_response = client.get("/api/v1/reports", headers=headers)
    print("Reports:", list_response.status_code)
    print("Count:", list_response.json()["count"])

    date_response = client.get(f"/api/v1/reports/{today.isoformat()}", headers=headers)
    print("By date:", date_response.status_code)
    print("By date body:", date_response.json())

    if date_response.status_code == 200:
        print(date_response.json()["recommendation"]["action"])

    run_now_response = client.post("/api/v1/reports/run-now", headers=headers)
    print("Run now:", run_now_response.status_code)
    print(run_now_response.json()["status"])

    assert health.status_code == 200
    assert today_response.status_code == 200
    assert list_response.status_code == 200
    assert date_response.status_code == 200
    assert run_now_response.status_code == 200
    assert run_now_response.json()["status"] == "not_implemented"

    print("API test OK")


if __name__ == "__main__":
    main()