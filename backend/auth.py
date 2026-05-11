import os

from fastapi import Header, HTTPException


def require_app_token(authorization: str | None = Header(default=None)) -> None:
    expected_token = os.getenv("APP_TOKEN", "").strip()

    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="APP_TOKEN is not configured on the server.",
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