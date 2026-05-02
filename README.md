# Algeria Verification Services (Monorepo)

This repository contains two specialized services for automated document verification and government website scraping in Algeria.

## Services

### 1. AI Service (Port 8001)
An agentic AI processing service that uses 6 specialized agents with multi-tool self-correction loops to verify documents.
- **Tech**: FastAPI, PaddleOCR, Tesseract, OpenCV, GPT-4o Vision.
- **Agents**: Classifier → OCR → Extraction → Authenticity → Consistency → Scoring.
- **Features**: SSE progress streaming, multi-engine OCR fallback, fuzzy name matching (Arabic/French).

### 2. Scraping Service (Port 8002)
A stateless scraping service that automates interactions with government portals (specifically CNAS).
- **Tech**: FastAPI, Playwright (Chromium), Tesseract OCR.
- **Features**: Browser pool management, CAPTCHA solving, rate limiting.

---

## Getting Started

### Prerequisites
- [uv](https://github.com/astral-sh/uv)
- Tesseract OCR (`sudo apt install tesseract-ocr`)
- System libs for OpenCV/Paddle (`libgl1`, `libglib2.0-0`)

### Installation
```bash
# Sync dependencies for both services (managed via uv workspaces)
uv sync
```

### Running Locally

**AI Service:**
```bash
cd ai-service
uv run uvicorn app.main:app --reload --port 8001
```

**Scraping Service:**
```bash
cd scraping-service
uv run uvicorn app.main:app --reload --port 8002
```

### Running with Docker

Each service has its own `Dockerfile`.

```bash
# Build AI Service
docker build -t ai-service ai-service/

# Build Scraping Service
docker build -t scraping-service scraping-service/
```

## Project Structure
- `ai-service/`: Agentic AI verification service.
- `scraping-service/`: External portal scraping service.
- `pyproject.toml`: Root configuration.
