# Scraping Service

A FastAPI-based stateless scraping service for government website verification.

## Features
- Playwright for browser automation
- OCR capabilities via Tesseract
- JSON logging
- Containerized with Docker and uv

## Getting Started

### Prerequisites
- [uv](https://github.com/astral-sh/uv)

### Installation
```bash
uv sync
```

### Running Locally
```bash
uv run uvicorn app.main:app --reload --port 8000
```

### Running with Docker
```bash
docker build -t scraping-service .
docker run -p 8000:8000 scraping-service
```

## Project Structure
- `app/`: FastAPI application code
- `tests/`: Project tests
- `Dockerfile`: Multi-stage build using uv
- `pyproject.toml`: Dependency management via uv
