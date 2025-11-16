# webhook/smart_sync.py - Smart Multi-User Sync API
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from starlette.requests import Request
from pydantic import BaseModel, Field

from core.auth import get_session_id
from clients.odoo_client import OdooClient, OdooError
from config import ODOO_URL

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/v2/sync", tags=["smart-sync"])

# ===== Schemas =====
class SyncRequest(BaseModel):
    user_id: int = Field(..., description="Odoo user ID")
    device_id: str = Field(..., min_length=1, max_length=255, description="Unique device identifier")
    app_type: str = Field(..., description="App type: sales_app, delivery_app, manager_app, etc.")
    models_filter: Optional[List[str]] = Field(None, description="Optional: filter by specific models")
    limit: int = Field(100, ge=1, le=500, description="Max events to fetch")

class EventData(BaseModel):
    id: int
    model: str
    record_id: int
    event: str
    timestamp: str

class SyncResponse(BaseModel):
    status: str = "success"
    has_updates: bool
    new_events_count: int
    events: List[EventData]
    next_sync_token: str
    last_sync_time: str

class SyncStatsResponse(BaseModel):
    user_id: int
    device_id: str
    last_event_id: int
    last_sync_time: str
    sync_count: int
    is_active: bool

# ===== Model Filters by App Type =====
APP_TYPE_MODELS = {
    "sales_app": [
        "sale.order",
        "res.partner",
        "product.template",
        "product.category",
    ],
    "delivery_app": [
        "stock.picking",
        "res.partner",
    ],
    "warehouse_app": [
        "stock.picking",
        "stock.move",
        "product.product",
    ],
    "manager_app": [
        "sale.order",
        "res.partner",
        "account.move",
        "purchase.order",
        "hr.expense",
    ],
    "mobile_app": [
        "sale.order",
        "res.partner",
        "product.template",
    ],
}

# ===== Dependencies =====
def get_client(session_id: str = Depends(get_session_id)) -> OdooClient:
    return OdooClient(
        base_url=ODOO_URL,
        session_id=session_id,
        timeout=15,
        retries=2,
        backoff=0.3,
        user_agent="SmartSyncAPI/2.0",
    )

def _get_limiter(request: Request) -> Limiter:
    return request.app.state.limiter

# ===== Routes =====
@router.post("/pull", response_model=SyncResponse)
def sync_pull(
    request: Request,
    sync_request: SyncRequest,
    client: OdooClient = Depends(get_client),
):
    """
    Smart sync - pulls only what the user needs based on their last sync state.
    Rate limited to 60 requests/minute per IP.
    """
    limiter: Limiter = _get_limiter(request)
    key = get_remote_address(request)
    if not limiter.hit("smart_sync_pull", key, limit=60, period=60):
        raise HTTPException(status_code=429, detail="Too many requests, slow down.")

    try:
        # 1. Get or create sync state for this user/device
        sync_state = client.call_kw(
            "user.sync.state",
            "get_or_create_state",
            [sync_request.user_id, sync_request.device_id, sync_request.app_type]
        )

        last_event_id = sync_state.get("last_event_id", 0)
        last_sync_time = sync_state.get("last_sync_time", "")

        # 2. Build domain for events
        domain = [
            ("id", ">", last_event_id),  # Only new events
            ("is_archived", "=", False),  # Only active events
        ]

        # Filter by app type models
        allowed_models = APP_TYPE_MODELS.get(sync_request.app_type, [])
        if allowed_models:
            domain.append(("model", "in", allowed_models))

        # Additional user filter
        if sync_request.models_filter:
            domain.append(("model", "in", sync_request.models_filter))

        # 3. Fetch events
        events = client.search_read(
            "update.webhook",
            domain=domain,
            fields=["id", "model", "record_id", "event", "timestamp"],
            limit=sync_request.limit,
            order="id asc"  # Oldest first for proper sync
        )

        if not events:
            return SyncResponse(
                has_updates=False,
                new_events_count=0,
                events=[],
                next_sync_token=str(last_event_id),
                last_sync_time=last_sync_time
            )

        # 4. Update user sync state
        new_last_event_id = events[-1]["id"]

        client.call_kw(
            "user.sync.state",
            "write",
            [[sync_state["id"]], {
                "last_event_id": new_last_event_id,
                "last_sync_time": client.call_kw("ir.fields", "get_current_datetime", []),
                "sync_count": sync_state.get("sync_count", 0) + 1
            }]
        )

        # 5. Mark events as synced by this user
        for event in events:
            try:
                client.call_kw(
                    "update.webhook",
                    "mark_as_synced_by_user",
                    [[event["id"]]]
                )
            except Exception as e:
                # Log but don't fail - non-critical
                print(f"Warning: Could not mark event {event['id']} as synced: {e}")

        # 6. Format response
        event_data = [
            EventData(
                id=e["id"],
                model=e.get("model", ""),
                record_id=e.get("record_id", 0),
                event=e.get("event", ""),
                timestamp=e.get("timestamp", "")
            )
            for e in events
        ]

        return SyncResponse(
            has_updates=True,
            new_events_count=len(events),
            events=event_data,
            next_sync_token=str(new_last_event_id),
            last_sync_time=last_sync_time
        )

    except OdooError as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e


@router.get("/state", response_model=SyncStatsResponse)
def get_sync_state(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    device_id: str = Query(..., description="Device ID"),
    client: OdooClient = Depends(get_client),
):
    """Get current sync state for a user/device"""
    limiter: Limiter = _get_limiter(request)
    key = get_remote_address(request)
    if not limiter.hit("sync_state", key, limit=30, period=60):
        raise HTTPException(status_code=429, detail="Too many requests, slow down.")

    try:
        states = client.search_read(
            "user.sync.state",
            domain=[
                ("user_id", "=", user_id),
                ("device_id", "=", device_id)
            ],
            fields=["user_id", "device_id", "last_event_id", "last_sync_time", "sync_count", "is_active"],
            limit=1
        )

        if not states:
            raise HTTPException(status_code=404, detail="Sync state not found")

        state = states[0]
        return SyncStatsResponse(
            user_id=state.get("user_id")[0] if isinstance(state.get("user_id"), list) else state.get("user_id"),
            device_id=state.get("device_id", ""),
            last_event_id=state.get("last_event_id", 0),
            last_sync_time=state.get("last_sync_time", ""),
            sync_count=state.get("sync_count", 0),
            is_active=state.get("is_active", False)
        )

    except HTTPException:
        raise
    except OdooError as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e


@router.post("/reset")
def reset_sync_state(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    device_id: str = Query(..., description="Device ID"),
    client: OdooClient = Depends(get_client),
):
    """Reset sync state for a user/device (useful for troubleshooting)"""
    limiter: Limiter = _get_limiter(request)
    key = get_remote_address(request)
    if not limiter.hit("sync_reset", key, limit=5, period=60):
        raise HTTPException(status_code=429, detail="Too many requests, slow down.")

    try:
        states = client.search(
            "user.sync.state",
            domain=[
                ("user_id", "=", user_id),
                ("device_id", "=", device_id)
            ]
        )

        if not states:
            raise HTTPException(status_code=404, detail="Sync state not found")

        client.write("user.sync.state", states, {
            "last_event_id": 0,
            "sync_count": 0
        })

        return {"status": "success", "message": "Sync state reset successfully"}

    except HTTPException:
        raise
    except OdooError as e:
        raise HTTPException(status_code=502, detail=f"Odoo error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") from e
