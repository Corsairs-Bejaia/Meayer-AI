FROM python:3.13-slim

# Install system dependencies for OpenCV, Tesseract, and Playwright
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    # Playwright / Chromium runtime deps
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv
ENV PATH="/uv/bin:${PATH}"

WORKDIR /app

# Copy workspace configuration
COPY pyproject.toml uv.lock ./

# Copy the ai-service package
COPY ai-service/ ./ai-service/

# Install dependencies for the whole workspace
RUN uv sync --frozen

# Install Playwright's Chromium browser
RUN uv run playwright install chromium --with-deps

# Set working directory to the service folder for execution
WORKDIR /app/ai-service

EXPOSE 8001

# PORT is injected by Railway at runtime; fall back to 8001 locally
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
