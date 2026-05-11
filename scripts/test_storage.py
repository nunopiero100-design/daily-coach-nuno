import datetime as dt
import shutil
from pathlib import Path

from backend.schemas import DailyCoachReport, Recommendation
from backend.storage import load_daily_report, list_daily_reports, save_daily_report


def main():
    test_dir = Path("tmp/test_reports")

    if test_dir.exists():
        shutil.rmtree(test_dir)

    report = DailyCoachReport(
        date=dt.date.today(),
        generated_at=dt.datetime.now(),
        status="GREEN",
        title="Teste storage",
        summary="Relatório de teste guardado em disco.",
        full_text="Texto completo do relatório de teste.",
        recommendation=Recommendation(
            action="KEEP",
            headline="Manter plano",
            details="Teste de gravação e leitura.",
        ),
    )

    saved_path = save_daily_report(report, reports_dir=test_dir)

    print(f"Saved: {saved_path}")

    loaded = load_daily_report(report.date.isoformat(), reports_dir=test_dir)
    print(f"Loaded status: {loaded['status']}")
    print(f"Loaded title: {loaded['title']}")

    reports = list_daily_reports(reports_dir=test_dir)
    print("Reports:")
    for path in reports:
        print(f"- {path}")

    assert saved_path.exists()
    assert loaded["status"] == "GREEN"
    assert loaded["title"] == "Teste storage"
    assert len(reports) == 1

    print("Storage test OK")


if __name__ == "__main__":
    main()