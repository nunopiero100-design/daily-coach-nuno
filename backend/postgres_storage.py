"""
Postgres-backed report storage - same table Nuno's own progress notes
originally proposed (daily_reports: report_date primary key, payload jsonb).

Matches the exact function contract backend/storage.py's JSON version uses,
so backend/storage.py can just delegate here when DATABASE_URL is set:
- save returns something str()-able (used for the API's "path" field)
- load returns a dict, or raises FileNotFoundError if there's no row
- list returns objects with a .stem attribute (matching Path.stem), newest
  first - ReportRef below is a minimal stand-in so callers written for
  Path objects (e.g. api.py's `path.stem`) work unchanged.
"""
import json

from psycopg2.extras import Json

from backend.db import ensure_schema, get_connection
from backend.schemas import DailyCoachReport


class ReportRef:
    def __init__(self, date_str: str):
        self.stem = date_str

    def __repr__(self):
        return f"ReportRef({self.stem})"


def save_daily_report_db(report: DailyCoachReport) -> str:
    conn = get_connection()
    try:
        ensure_schema(conn)
        payload = report.model_dump(mode="json")
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into daily_reports (report_date, payload, updated_at)
                values (%s, %s, now())
                on conflict (report_date)
                do update set payload = excluded.payload, updated_at = now();
                """,
                (report.date.isoformat(), Json(payload)),
            )
        conn.commit()
    finally:
        conn.close()
    return f"postgres:daily_reports:{report.date.isoformat()}"


def load_daily_report_db(report_date: str) -> dict:
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "select payload from daily_reports where report_date = %s;",
                (report_date,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise FileNotFoundError(f"Report not found: {report_date}")
    return row[0]


def list_daily_reports_db() -> list[ReportRef]:
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("select report_date from daily_reports order by report_date desc;")
            rows = cur.fetchall()
    finally:
        conn.close()

    return [ReportRef(r[0].isoformat()) for r in rows]


def save_feedback_db(feedback) -> str:
    conn = get_connection()
    try:
        ensure_schema(conn)
        payload = json.loads(feedback.model_dump_json())
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into feedback_entries (feedback_date, feedback_type, note, payload)
                values (%s, %s, %s, %s);
                """,
                (feedback.date.isoformat(), feedback.type, feedback.note, Json(payload)),
            )
        conn.commit()
    finally:
        conn.close()
    return f"postgres:feedback_entries:{feedback.date.isoformat()}"


def load_feedback_for_date_db(feedback_date: str) -> list[dict]:
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "select payload from feedback_entries where feedback_date = %s order by created_at;",
                (feedback_date,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def list_feedback_db() -> list[dict]:
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("select payload from feedback_entries order by feedback_date desc, created_at desc;")
            rows = cur.fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def save_device_token_db(token: str, platform: str) -> None:
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into device_tokens (token, platform)
                values (%s, %s)
                on conflict (token) do update set platform = excluded.platform;
                """,
                (token, platform),
            )
        conn.commit()
    finally:
        conn.close()


def list_device_tokens_db() -> list[str]:
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("select token from device_tokens;")
            rows = cur.fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]
