# Corsairs-Bejaia: AI Verification Service

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

> **High-fidelity automated document verification for the Algerian market.** Combining sophisticated agentic AI orchestration with robust government portal automation natively in a single microservice.

---

## Overview

This repository powers a high-integrity document verification pipeline. It is designed to replace manual review with an **Agentic Autonomous System** that classifies, extracts, and validates documents while detecting fraud, cross-referencing government data (CNAS) via web scraping, and generating professional reports.

---

## Documentation

Detailed documentation is available in the [docs/](docs/) folder:

### Architecture & Design
- **[System Architecture](docs/architecture.md)**: A short explanation of the core architecture.
- **[System Architecture Diagram](docs/system_architecture_diagram.md)**: A Mermaid-based technical flow of the pipeline.
- **[Visual Representation](docs/visual_representation.md)**: A high-level visual view of the system ecosystem.
- **[Components & Interactions](docs/components_and_interactions.md)**: Deep dive into how agents, tools, and the context interact.

### Code & Setup
- **[Clean Code Structure](docs/clean_code.md)**: Explanation of the project layout and design patterns.
- **[Setup Instructions](docs/setup.md)**: How to get the service running locally with `uv`.

---

## Core Features

*   **7-Agent Pipeline**: Specialized agents for Classification, OCR, Extraction, Authenticity, Consistency, Scraping, and Scoring.
*   **Government Portal Automation**: Native scraping for `elhanaa.cnas.dz` to verify employment records.
*   **Fraud Detection**: ELA analysis, stamp detection, and AI-generation artifact checks.
*   **Self-Correction**: Automatic tool fallback (e.g., Tesseract -> Gemini) on low confidence.
*   **Real-time SSE**: Pipeline progress streaming for frontend clients.

---

## Quick Start

```bash
# Install dependencies
uv sync
uv run playwright install chromium

# Run the service
uv run uvicorn app.main:app --port 8000 --reload
```

*For more detailed instructions, see [Setup Guide](docs/setup.md).*

---
Corsairs-Bejaia Verification Service - 2026 Hackathon.
