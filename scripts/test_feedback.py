import datetime as dt
import shutil
from pathlib import Path

from backend.feedback import (
    FeedbackEntry,
    list_feedback,
    load_feedback_for_date,
    save_feedback,
)


def main():
    test_dir = Path("tmp/test_feedback")

    if test_dir.exists():
        shutil.rmtree(test_dir)

    today = dt.date.today()

    feedback_1 = FeedbackEntry(
        date=today,
        type="NO_TIME",
        note="Só tenho 45 minutos hoje.",
    )

    feedback_2 = FeedbackEntry(
        date=today,
        type="RAIN_INDOOR",
        note="Chuva, provavelmente rolo.",
    )

    path_1 = save_feedback(feedback_1, feedback_dir=test_dir)
    path_2 = save_feedback(feedback_2, feedback_dir=test_dir)

    print(f"Saved 1: {path_1}")
    print(f"Saved 2: {path_2}")

    entries_today = load_feedback_for_date(today.isoformat(), feedback_dir=test_dir)
    all_entries = list_feedback(feedback_dir=test_dir)

    print(f"Entries today: {len(entries_today)}")
    print(f"All entries: {len(all_entries)}")
    print(entries_today)

    assert path_1 == path_2
    assert len(entries_today) == 2
    assert entries_today[0]["type"] == "NO_TIME"
    assert entries_today[1]["type"] == "RAIN_INDOOR"
    assert len(all_entries) == 2

    print("Feedback test OK")


if __name__ == "__main__":
    main()