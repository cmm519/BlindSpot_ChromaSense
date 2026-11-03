"""Anonymous session ID for each browser, kept in a cookie."""

import re
import secrets

from fastapi import Request, Response

COOKIE_NAME = "chromasense_session"
_VALID_ID = re.compile(r"[A-Za-z0-9_-]{16,128}")


def session_id_from(request: Request) -> tuple[str, bool]:
    """Return the session ID for a request, and whether it is new."""
    existing = request.cookies.get(COOKIE_NAME, "")
    if _VALID_ID.fullmatch(existing):
        return existing, False
    return secrets.token_urlsafe(32), True


def set_session_cookie(response: Response, session_id: str) -> None:
    # The portal uses plain HTTP on the LAN, so the cookie cannot be Secure.
    response.set_cookie(COOKIE_NAME, session_id, httponly=True, samesite="lax")
