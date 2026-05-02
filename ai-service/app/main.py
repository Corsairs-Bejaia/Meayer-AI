import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from pythonjsonlogger import jsonlogger
from app.config import settings

# Configure logging
logger = logging.getLogger()
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(settings.LOG_LEVEL.upper())

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up {settings.SERVICE_NAME}...")
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}...")

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "agents_loaded": ["classifier", "ocr", "extraction", "authenticity", "consistency", "scoring"]
    }

from app.routers import pipeline

app.include_router(pipeline.router, prefix="/api")
