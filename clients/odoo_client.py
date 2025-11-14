import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

logger = logging.getLogger(__name__)


class OdooError(RuntimeError):
    """Raised when Odoo returns an application-level error."""
    def __init__(self, message: str, *, code: Optional[str] = None, data: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.data = data or {}


class OdooClient:
    """Lightweight Odoo client using session-based auth.

    - Prefers /web/dataset/call_kw with session cookie (recommended for session auth).
    - Provides a minimal /jsonrpc helper when needed.
    - Includes retry with backoff for transient network errors.
    """

    def __init__(
        self,
        base_url: str,
        session_id: Optional[str] = None,
        *,
        db: Optional[str] = None,
        timeout: float = 15.0,
        retries: int = 2,
        backoff: float = 0.3,
        extra_headers: Optional[Dict[str, str]] = None,
        user_agent: Optional[str] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.db = db
        self.retries = max(0, int(retries))
        self.backoff = max(0.0, float(backoff))

        headers = {"Content-Type": "application/json"}
        if user_agent:
            headers["User-Agent"] = user_agent
        if extra_headers:
            headers.update(extra_headers)

        cookies = {}
        if session_id:
            cookies["session_id"] = session_id

        self._client = httpx.Client(
            timeout=timeout,
            headers=headers,
            cookies=cookies,
            transport=transport,
        )

    # -----------------------------
    # Low-level HTTP with retries
    # -----------------------------
    def _post_json(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Standard JSON-RPC envelope may include "error"
                if isinstance(data, dict) and "error" in data:
                    err = data["error"]
                    # Odoo error format: {'code': ..., 'message': ..., 'data': {...}}
                    raise OdooError(
                        err.get("message", "Odoo RPC error"),
                        code=str(err.get("code", "")),
                        data=err.get("data") or {},
                    )
                return data
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                if attempt < self.retries:
                    sleep_for = self.backoff * (2 ** attempt)
                    logger.warning(
                        "POST %s failed (attempt %d/%d): %s; retrying in %.2fs",
                        path, attempt + 1, self.retries + 1, exc, sleep_for
                    )
                    time.sleep(sleep_for)
                else:
                    break
        assert last_exc is not None
        raise last_exc

    # -----------------------------
    # JSON-RPC helpers (optional)
    # -----------------------------
    def _jsonrpc(self, service: str, method: str, args: list, kwargs: Optional[dict] = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": args, "kwargs": kwargs or {}},
            "id": 1,
        }
        data = self._post_json("/jsonrpc", payload)
        # Successful JSON-RPC responses carry "result"
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        # Some endpoints (mis)respond without envelope; return raw
        return data

    # -----------------------------
    # call_kw (preferred for session cookie)
    # -----------------------------
    def call_kw(self, model: str, method: str, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """Call an Odoo model method via /web/dataset/call_kw.

        This requires a valid session cookie established on this client.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {},
            },
            "id": 1,
        }
        data = self._post_json("/web/dataset/call_kw", payload)
        # Standard envelope: {'jsonrpc':'2.0','id':1,'result':...}
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data

    # -----------------------------
    # High-level convenience APIs
    # -----------------------------
    def is_session_valid(self) -> bool:
        """Check if the session is valid by calling a light endpoint."""
        try:
            # /web/session/get_session_info returns info when session is valid
            data = self._post_json(
                "/web/session/get_session_info",
                {"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}
            )
            return isinstance(data, dict) and data.get("result") is not None
        except Exception:
            return False

    def search(self, model: str, domain: List, *, limit: Optional[int] = None, offset: int = 0, order: Optional[str] = None) -> List[int]:
        kwargs: Dict[str, Any] = {"offset": offset}
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self.call_kw(model, "search", [domain], kwargs)

    def read(self, model: str, ids: List[int], fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        return self.call_kw(model, "read", [ids], kwargs)

    def search_read(
        self,
        model: str,
        domain: List,
        fields: Optional[List[str]] = None,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        order: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {"offset": offset}
        if fields:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        if context:
            kwargs["context"] = context
        return self.call_kw(model, "search_read", [domain], kwargs)

    def create(self, model: str, vals_list: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[int, List[int]]:
        if isinstance(vals_list, dict):
            # single record
            return self.call_kw(model, "create", [vals_list])
        return self.call_kw(model, "create", [vals_list])

    def write(self, model: str, ids: List[int], vals: Dict[str, Any]) -> bool:
        return bool(self.call_kw(model, "write", [ids, vals]))

    def unlink(self, model: str, ids: List[int]) -> bool:
        return bool(self.call_kw(model, "unlink", [ids]))

    def name_get(self, model: str, ids: List[int]) -> List[Tuple[int, str]]:
        return self.call_kw(model, "name_get", [ids])

    def fields_get(self, model: str, attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.call_kw(model, "fields_get", [], {"attributes": attributes or []})

    # -----------------------------
    # Utilities for update.webhook
    # -----------------------------
    # --- inside OdooClient.get_updates_summary ---
    def get_updates_summary(self, *, limit: int = 200, since: Optional[str] = None) -> Dict[str, Any]:
        domain: List = []
        if since:
            domain.append(["timestamp", ">=", since])  # بدل occurred_at → timestamp
        rows = self.search_read(
            "update.webhook",
            domain=domain,
            fields=["model", "record_id", "event", "timestamp"],  # هنا أيضًا
            limit=limit,
            order="timestamp desc",  # هنا أيضًا
        )
        last_at = rows[0].get("timestamp") if rows else None  # هنا أيضًا
        tally: Dict[str, int] = {}
        for r in rows:
            m = r.get("model") or "?"
            tally[m] = tally.get(m, 0) + 1
        summary = [{"model": m, "count": c} for m, c in tally.items()]
        return {"last_update_at": last_at, "summary": summary, "events": rows}

    # --- inside OdooClient.cleanup_updates ---
    def cleanup_updates(self, *, before: Optional[str] = None) -> int:
        domain: List = []
        if before:
            domain.append(["timestamp", "<=", before])  # بدل occurred_at → timestamp
        ids = self.call_kw("update.webhook", "search", [domain])
        if not ids:
            return 0
        return int(self.call_kw("update.webhook", "unlink", [ids])) or 0


    # -----------------------------
    # Context manager
    # -----------------------------
    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    def __enter__(self) -> "OdooClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
