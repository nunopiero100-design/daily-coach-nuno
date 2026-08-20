import os

from fastapi import Header, HTTPException


def _check_bearer_token(authorization: str | None, expected_token: str, config_name: str) -> None:
    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail=f"{config_name} is not configured on the server.",
        )

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header.",
        )

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format.",
        )

    provided_token = authorization[len(prefix):].strip()

    if provided_token != expected_token:
        raise HTTPException(
            status_code=403,
            detail="Invalid token.",
        )


def require_app_token(authorization: str | None = Header(default=None)) -> None:
    expected_token = os.getenv("APP_TOKEN", "").strip()
    _check_bearer_token(authorization, expected_token, "APP_TOKEN")


def require_ingest_token(authorization: str | None = Header(default=None)) -> None:
    """
    Separate from APP_TOKEN on purpose: the mobile app only ever needs to
    READ reports, so it only ever holds APP_TOKEN. Only daily_coach_agent.py
    (running in GitHub Actions) holds INGEST_TOKEN and can WRITE a new report.
    If the app's token ever leaked, it couldn't be used to inject fake reports.
    """
    expected_token = os.getenv("INGEST_TOKEN", "").strip()
    _check_bearer_token(authorization, expected_token, "INGEST_TOKEN")