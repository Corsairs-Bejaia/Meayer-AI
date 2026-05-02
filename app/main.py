import logging
import sys
import httpx
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from pythonjsonlogger import jsonlogger

from app.config import settings
from app.dependencies import verify_api_key
from app.routers import cnas, stubs

logger = logging.getLogger()
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(settings.LOG_LEVEL.upper())

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.browser_pool import browser_pool
    await browser_pool.start()
    yield
    await browser_pool.stop()

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="""
    A high-performance scraping service for government website verification.
    
    ### Features:
    * **CNAS Verification**: Employer and employee status checks.
    * **Automated OCR**: Built-in CAPTCHA solving via Tesseract and Gemini.
    * **Browser Pool**: Efficient Playwright context management.
    """,
    version=settings.VERSION,
    contact={
        "name": "Corsairs Bejaia",
        "url": "https://github.com/Corsairs-Bejaia",
    },
    openapi_tags=[
        {
            "name": "cnas",
            "description": "National Social Security Fund (CNAS) automation endpoints.",
        },
        {
            "name": "stubs",
            "description": "Endpoints planned for future implementation.",
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.get("/api/health")
async def health_check():
    external_cnas = {"reachable": False, "response_time_ms": 0}
    try:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(settings.CNAS_BASE_URL)
            external_cnas["reachable"] = response.status_code < 500
            external_cnas["response_time_ms"] = int((time.monotonic() - start) * 1000)
    except Exception:
        pass

    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "external": {
            "cnas": external_cnas
        }
    }

app.include_router(cnas.router, prefix="/api")
app.include_router(stubs.router)
