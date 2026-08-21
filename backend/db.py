"""
Postgres connection helper for the daily_reports persistence layer.

Only used when DATABASE_URL is set (Supabase or any other Postgres). When
it isn't set, backend/storage.py falls back to local JSON files - this
module is never imported in that case, so psycopg2 not being installed
would never break the local-JSON path.
"""
import os


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def is_postgres_configured() -> bool:
    return bool(get_database_url())


def get_connection():
    import psycopg2  # local import: only needed when Postgres is actually configured

    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set.")
    return psycopg2.connect(database_url)


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            create table if not exists daily_reports (
                report_date date primary key,
                payload jsonb not null,
                created_at timestamptz not null default now(),
                updated_at timestamptz not null default now()
            );
            """
        )
        cur.execute(
            """
            create table if not exists feedback_entries (
                id bigserial primary key,
                feedback_date date not null,
                feedback_type text not null,
                note text,
                payload jsonb not null,
                created_at timestamptz not null default now()
            );
            """
        )
        cur.execute(
            "create index if not exists idx_feedback_entries_date on feedback_entries (feedback_date);"
        )
        cur.execute(
            """
            create table if not exists device_tokens (
                token text primary key,
                platform text not null,
                created_at timestamptz not null default now()
            );
            """
        )
    conn.commit()
