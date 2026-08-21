"""
Sends push notifications via Firebase Cloud Messaging.

Uses the firebase-admin SDK (handles the OAuth2/JWT exchange for the
modern FCM v1 API internally, rather than hand-rolling that flow) and a
service-account key - NOT the same file as google-services.json, which is
client-side only. Get the service account key from Firebase Console ->
Project Settings (gear icon) -> Service accounts -> Generate new private key.

Set it as one environment variable, EITHER as:
    FIREBASE_SERVICE_ACCOUNT_JSON = <paste the entire file content as-is>
OR (safer - avoids any risk of a host mangling the embedded line breaks in
the private key when pasting multi-line text):
    FIREBASE_SERVICE_ACCOUNT_JSON = <the file, base64-encoded, as one line>
Both are accepted transparently - see _parse_credential() below.

If neither is set, send_push_to_all_devices() silently does nothing - so
this can ship and be deployed before the credential exists, same as the
other external-service patterns today (Supabase, GitHub token).
"""
import base64
import json
import os

from backend.devices import list_device_tokens

_firebase_app = None  # lazily initialized, cached across calls in the same process


def _parse_credential(raw: str) -> dict:
    """Accepts either raw JSON or base64-encoded JSON, tries raw first."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        decoded = base64.b64decode(raw).decode("utf-8")
        return json.loads(decoded)


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None

    import firebase_admin
    from firebase_admin import credentials

    cred_dict = _parse_credential(raw)
    cred = credentials.Certificate(cred_dict)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_push_to_all_devices(title: str, body: str) -> tuple[int, int]:
    """
    Best-effort: sends to every registered device token. Returns
    (success_count, failure_count). Never raises - a push failure should
    never break report ingestion, which is what calls this.
    """
    app = _get_firebase_app()
    if app is None:
        return (0, 0)

    tokens = list_device_tokens()
    if not tokens:
        return (0, 0)

    from firebase_admin import messaging

    success, failure = 0, 0
    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=token,
            )
            messaging.send(message)
            success += 1
        except Exception as e:
            print(f"Aviso: push falhou para um dispositivo: {e}")
            failure += 1
    return (success, failure)
