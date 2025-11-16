# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Rate limiting (slowapi)
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

from webhook.update_webhook import router as updates_router
from webhook.webhook import router as webhook_router
from webhook.smart_sync import router as smart_sync_router

# ==========================
# Initialize FastAPI
# ==========================
app = FastAPI(
    title="Odoo Webhook Server",
    version="2.0.0",
    description="API for Odoo webhooks integration with Multi-User Smart Sync",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==========================
# CORS (restrict in production)
# ==========================
ALLOWED_ORIGINS = [
    "https://app.propanel.ma",
    "https://flutter.propanel.ma",
    "https://webhook.geniura.com",
    "http://localhost:3000",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ==========================
# Rate Limiting (slowapi)
# ==========================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests, please slow down."},
    )

app.add_middleware(SlowAPIMiddleware)

# ==========================
# Routers
# ==========================
app.include_router(updates_router)      # /api/v1/check-updates , /api/v1/cleanup
app.include_router(webhook_router)      # /api/v1/webhook/events
app.include_router(smart_sync_router)   # /api/v2/sync/* (NEW - Smart Multi-User Sync)

# ==========================
# Health check
# ==========================
@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to Odoo Webhook Server",
        "status": "running",
        "version": "2.0.0",
        "services": {
            "webhook": "active",
            "check_updates": "active",
            "cleanup": "active",
            "smart_sync": "active"  # NEW
        },
        "endpoints": {
            "v1": ["/api/v1/webhook/events", "/api/v1/check-updates", "/api/v1/cleanup"],
            "v2": ["/api/v2/sync/pull", "/api/v2/sync/state", "/api/v2/sync/reset"]
        }
    }