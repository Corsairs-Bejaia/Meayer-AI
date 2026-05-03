FROM python:3.11-slim

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

# Copy dependency files
COPY pyproject.toml uv.lock .env* ./

# Copy application source
COPY app/ ./app/
COPY static/ ./static/

# Install dependencies
RUN uv sync --frozen

# Install Playwright's Chromium browser
RUN uv run playwright install chromium --with-deps

EXPOSE 8000

# Use explicit shell to ensure $PORT is expanded
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
