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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the dependency manifest first (better layer caching)
COPY pyproject.toml .

# Install all Python dependencies declared in pyproject.toml
# pip reads [project].dependencies directly — no requirements.txt needed
RUN pip install --no-cache-dir .

# Install Playwright's Chromium browser + its own deps
RUN playwright install chromium --with-deps

# Copy application source
COPY . .

EXPOSE 8001

# PORT is injected by Railway at runtime; fall back to 8001 locally
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
