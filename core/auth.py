# core/auth.py
from fastapi import Header, Request, HTTPException

HEADER_NAME = "X-Session-Id"
COOKIE_NAME = "session_id"

def get_session_id(
    request: Request,
    x_session_id: str | None = Header(default=None, alias=HEADER_NAME),
) -> str:
    """
    Preferred: Header X-Session-Id
    Fallback:  Cookie session_id
    """
    sid = x_session_id or request.cookies.get(COOKIE_NAME)
    if not sid:
        # توحيد رسالة الخطأ عبر المشروع
        raise HTTPException(status_code=401, detail="BAD_SESSION: missing session id")
    # فلتر بسيط (اختياري) لتجنّب مدخلات غريبة جدًا
    if len(sid) > 256:
        raise HTTPException(status_code=400, detail="INVALID_SESSION: too long")
    return sid
