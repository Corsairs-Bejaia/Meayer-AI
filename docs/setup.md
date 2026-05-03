# Installation & Setup

This guide will help you get the AI Verification Service running on your local machine.

## Prerequisites

- **Python 3.13+**
- **uv**: The fastest Python package manager. [Install uv here](https://github.com/astral-sh/uv).
- **System Dependencies**:
  ```bash
  sudo apt update && sudo apt install tesseract-ocr libgl1 libglib2.0-0
  ```

## Local Development Setup

### 1. Clone and Enter Directory
```bash
git clone <repository-url>
cd ai-service
```

### 2. Install Dependencies
`uv` will automatically create a virtual environment and install all packages from `pyproject.toml`.
```bash
uv sync
```

### 3. Install Playwright Browsers
Required for the `ScrapingAgent`.
```bash
uv run playwright install chromium
```

### 4. Configure Environment
Copy the example environment file and fill in your API keys (especially `GOOGLE_API_KEY` for Gemini).
```bash
cp .env.example .env
```

### 5. Run the Service
Start the FastAPI server with hot-reload enabled.
```bash
uv run uvicorn app.main:app --port 8000 --reload
```

## Running Tests
Ensure the system is working correctly by running the full test suite.
```bash
uv run pytest tests
```
