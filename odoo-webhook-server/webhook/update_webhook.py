# webhook/update_webhook.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from starlette.requests import Request

from core.auth import get_session_id
from clients.odoo_client import OdooClient, OdooError
from pydantic import BaseModel
from config import ODOO_URL  # تأكد من وجوده في config.py

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/v1", tags=["updates"])

# ===== Schemas =====
class ModelCount(BaseModel):
    model: str
    count: int

class CheckUpdatesOut(BaseModel):
    has_update: bool
    last_update_at: Optional[str] = None
    summary: list[ModelCount]

# ===== Dependencies =====
def get_client(session_id: str = Depends(get_session_id)) -> OdooClient:
    return OdooClient(
        base_url=ODOO_URL,
        session_id=session_id,
        timeout=15,
        retries=2,
        backoff=0.3,
        user_agent="WebhookServer/1.0",
    )

def _get_limiter(request: Request) -> Limiter:
    # نأخذ ال-limiter المُسجل في app.state (مُهيّأ في main.py)
    return request.app.state.limiter

# ===== Routes =====
@router.get("/check-updates", response_model=CheckUpdatesOut)
def check_updates(
    request: Request,  # ضروري لالتقاط IP من أجل التحديد
    since: Optional[str] = Query(None, description="ISO datetime: return updates >= since"),
    limit: int = Query(200, ge=1, le=1000),
    client: OdooClient = Depends(get_client),
):
    """
    Returns a lightweight summary of update.webhook since a timestamp (optional).
    Rate limited to 10 requests/minute per IP.
    """
    # Rate limiting handled by SlowAPIMiddleware in main.py

    try:
        data = client.get_updates_summary(limit=limit, since=since)
    except OdooError as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}") from e

    last_at = data.get("last_update_at")
    summary = [ModelCount(**s) for s in data.get("summary", [])]
    return CheckUpdatesOut(
        has_update=bool(summary),
        last_update_at=last_at,
        summary=summary
    )

@router.delete("/cleanup")
def cleanup_updates(
    request: Request,
    before: Optional[str] = Query(None, description="Delete events occurred_at <= before (ISO datetime)"),
    client: OdooClient = Depends(get_client),
):
    """
    Cleanup update.webhook rows older than a given ISO timestamp.
    Rate limited to 5 requests/minute per IP.
    """
    # Rate limiting handled by SlowAPIMiddleware in main.py

    try:
        deleted = client.cleanup_updates(before=before)
    except OdooError as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}") from e

    return {"ok": True, "deleted": deleted}

@router.get("/health")
def health():
    return {"status": "ok"}
