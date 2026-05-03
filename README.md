# Corsairs-Bejaia: AI Verification Service

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

> **The next generation of trust for the Algerian digital economy.** An autonomous, multi-agent system designed to verify, cross-reference, and authenticate documents with native government portal integration.

---

## Overview

This repository houses a sophisticated document verification engine. It moves beyond simple OCR by utilizing a **reasoning-based agentic architecture** to handle the complexities of Algerian administrative documents, forgery detection, and live government verification.

---

## Why an Agentic System?

Traditional document processing pipelines are brittle—if a single regex fails or an image is slightly blurry, the whole process breaks. We chose an **Agentic System** because:

1.  **Resilience through Reasoning**: Our agents don't just follow scripts; they make decisions. If Tesseract fails to read a blurry ID, the OCR Agent "decides" to invoke Gemini Vision for a more expensive but accurate recovery.
2.  **Autonomous Problem Solving**: Navigating government portals like `elhanaa.cnas.dz` requires handling dynamic states and CAPTCHAs. Our Scraping Agent acts as a virtual operator, managing browser sessions autonomously.
3.  **Modular Scalability**: New document types or verification layers can be added as specialized agents without refactoring the core pipeline.

---

## Human-in-the-Loop (HITL)

We believe in **AI-Augmented Trust**, not just AI automation. Our system is designed with safety at its core:

-   **Confidence Thresholds**: Every decision is backed by a confidence score. If an agent is unsure (e.g., < 80% confidence), the system automatically flags the request for human review.
-   **Transparency & Auditability**: Every verification includes a "trace"—a microscopic log of every tool used, every thought process, and every piece of evidence gathered. Humans can step in, view the evidence, and make the final call with 100% clarity.
-   **Explainable Decisions**: Instead of a "Yes/No," the system provides reasoning: *"Rejected: NIN mismatch detected between Identity Card and Medical Diploma."*

---

## Why This Wins

This project isn't just a technical exercise; it's a solution to a multi-million dollar problem in Algeria. Here is what makes this a winning entry:

1.  **Native Government Integration**: We have successfully automated the "last mile" by integrating live scraping of CNAS/CASNOS portals—a feat that traditional AI services cannot achieve.
2.  **Deep Local Context**: Built specifically for the Algerian market, handling Arabic/French transliterations and local document formats that generic global providers fail to recognize.
3.  **Production-Ready Forensic Layer**: Our Authenticity Agent uses ELA (Error Level Analysis) and AI-generation detection to catch sophisticated digital forgeries, moving beyond simple image checks.
4.  **Optimized Performance**: Managed via `uv` and utilizing parallel agent execution, the system delivers sub-10-second comprehensive verifications.

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
- **[Deployment Guide](docs/deployment.md)**: Instructions for deploying to **Railway** and Docker.

---

## Deployment

The service is production-ready and optimized for **Railway**. It utilizes a global `Dockerfile` and `railway.toml` at the root for seamless, zero-config deployment.

To deploy:
1. Push this repo to GitHub.
2. Connect your repo to [Railway](https://railway.app/).
3. Add your `GOOGLE_API_KEY` to the environment variables.

See the **[Deployment Guide](docs/deployment.md)** for more details.

---

## Quick Start

```bash
# Install dependencies
uv sync
uv run playwright install chromium

# Run the service
uv run uvicorn app.main:app --port 8000 --reload
```

---
Corsairs-Bejaia Verification Service - 2026 Hackathon.
