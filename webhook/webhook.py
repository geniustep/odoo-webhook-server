# webhook/webhook.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Literal
from starlette.requests import Request

from core.auth import get_session_id
from clients.odoo_client import OdooClient, OdooError
from pydantic import BaseModel
from config import ODOO_URL

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/v1/webhook", tags=["webhook"])

# ===== Schemas =====
class WebhookEventOut(BaseModel):
    id: int
    model: str
    record_id: int
    event: Literal["create", "write", "unlink", "manual"]
    occurred_at: str   # نظهره هكذا للعميل (لكن مصدره من timestamp)

class EventsResponse(BaseModel):
    status: str = "success"
    count: int
    data: list[WebhookEventOut]

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

# ===== Routes =====
@router.get("/events", response_model=EventsResponse)
def list_events(
    request: Request,
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    record_id: Optional[int] = Query(None, description="Filter by specific record id"),
    event: Optional[str] = Query(None, description="create|write|unlink|manual"),
    since: Optional[str] = Query(None, description="ISO datetime to filter timestamp >= since"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    client: OdooClient = Depends(get_client),
):
    """
    List raw events from update.webhook with useful filters.
    Rate limited to 30 requests/minute per IP.
    """
    # Rate limiting (30 طلب/دقيقة لكل IP)
    limiter: Limiter = request.app.state.limiter
    key = get_remote_address(request)
    if not limiter.hit("webhook_events", key, limit=30, period=60):
        raise HTTPException(status_code=429, detail="Too many requests, slow down.")

    # Build domain
    domain = []
    if model_name:
        domain.append(["model", "=", model_name])
    if record_id is not None:
        domain.append(["record_id", "=", record_id])
    if event:
        domain.append(["event", "=", event])
    if since:
        domain.append(["timestamp", ">=", since])  # ✅ استبدلنا occurred_at بـ timestamp

    try:
        rows = client.search_read(
            "update.webhook",
            domain=domain,
            fields=["id", "model", "record_id", "event", "timestamp"],  # ✅ استبدال
            limit=limit,
            offset=offset,
            order="timestamp desc",  # ✅ استبدال
        )
    except OdooError as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}") from e

    # ✅ نعرض timestamp لكن تحت اسم occurred_at
    data = [
        WebhookEventOut(
            id=r["id"],
            model=r.get("model", ""),
            record_id=r.get("record_id", 0),
            event=r.get("event", "manual"),
            occurred_at=r.get("timestamp", ""),
        )
        for r in rows
    ]
    return EventsResponse(count=len(data), data=data)
