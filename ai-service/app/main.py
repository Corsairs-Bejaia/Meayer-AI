import logging
import sys
import time
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pythonjsonlogger import jsonlogger

from app.config import settings
from app.routers import pipeline, classify, extract, authenticity, consistency, score, templates

# ── Logging setup ──
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(settings.LOG_LEVEL.upper())


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title="AI Verification Service",
    description=(
        "Agentic document verification: classification → OCR → extraction "
        "→ authenticity → consistency → scoring. "
        "6 specialized agents with multi-tool self-correction loops."
    ),
    openapi_tags=[
        {"name": "pipeline", "description": "Full agentic pipeline — all 6 agents."},
        {"name": "classify", "description": "Document type classification."},
        {"name": "extract", "description": "Template-aware field extraction."},
        {"name": "authenticity", "description": "Forgery and tampering detection."},
        {"name": "consistency", "description": "Cross-document validation."},
        {"name": "score", "description": "Trust score calculation."},
        {"name": "templates", "description": "Predefined document schemas."},
    ],
    # Disable default docs to override with unified version below
    docs_url=None,
    redoc_url="/redoc",
)

# ── Unified Swagger UI ──
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse

@app.get("/docs", include_in_schema=False)
async def unified_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=None, # Set to None when using 'urls' parameter
        title=app.title + " - Unified Docs",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "urls": [
                {"url": "/openapi.json", "name": "1. AI Verification Service"},
                {"url": "/api/scraping/openapi.json", "name": "2. Scraping Service (Port 8002)"},
            ],
            "layout": "StandaloneLayout" # Required for the top bar switcher
        },
    )

@app.get("/api/scraping/openapi.json", include_in_schema=False)
async def proxy_scraping_openapi():
    """Proxies the scraping service OpenAPI JSON for the unified Swagger UI."""
    async with httpx.AsyncClient() as client:
        try:
            # Note: Port 8002 must be running
            resp = await client.get("http://localhost:8002/openapi.json", timeout=2.0)
            return JSONResponse(content=resp.json())
        except Exception:
            return JSONResponse(content={"error": "Scraping service unreachable on port 8002"}, status_code=503)

# ── Health ──
@app.get("/api/health", tags=["health"])
async def health_check():
    cnas_reachable = False
    cnas_ms = 0
    try:
        t = time.monotonic()
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.head("https://teledeclaration.cnas.dz")
            cnas_reachable = r.status_code < 500
            cnas_ms = int((time.monotonic() - t) * 1000)
    except Exception:
        pass

    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "agents_loaded": [
            "classifier", "ocr", "extraction",
            "authenticity", "consistency", "scoring",
        ],
        "gemini_enabled": settings.ENABLE_GEMINI_FALLBACK,
        "external": {"cnas": {"reachable": cnas_reachable, "response_time_ms": cnas_ms}},
    }


# ── Metrics ──
@app.get("/api/metrics", tags=["health"])
async def metrics():
    """Lightweight operational metrics."""
    return {
        "service": settings.SERVICE_NAME,
        "gemini_enabled": settings.ENABLE_GEMINI_FALLBACK,
        "confidence_threshold": settings.DEFAULT_CONFIDENCE_THRESHOLD,
        "max_self_correction_retries": settings.MAX_SELF_CORRECTION_RETRIES,
    }


# ── Routers ──
app.include_router(pipeline.router, prefix="/api")
app.include_router(classify.router, prefix="/api")
app.include_router(extract.router, prefix="/api")
app.include_router(authenticity.router, prefix="/api")
app.include_router(consistency.router, prefix="/api")
app.include_router(score.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
