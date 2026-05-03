# Project Structure

The project follows a modular, agentic architecture designed for scalability, maintainability, and clear separation of concerns.

## Directory Layout

```text
ai-service/
├── app/
│   ├── agents/          # Specialized AI agents (Classifier, OCR, etc.)
│   ├── routers/         # API endpoints (FastAPI)
│   ├── services/        # Shared services (Browser Pool, Layer Registry)
│   ├── tools/           # Atomic tools used by agents (Tesseract, Gemini, etc.)
│   ├── config.py        # Environment-driven configuration
│   └── main.py          # FastAPI application entry point
├── tests/               # Comprehensive test suite
├── docs/                # Extended documentation
└── pyproject.toml       # Dependency management via uv
```

## Core Design Patterns

### 1. The Agent Pattern
Each agent inherits from `BaseAgent` and is responsible for a single domain (e.g., `ExtractionAgent`). This makes the system extremely modular—adding a new verification step is as simple as creating a new agent and registering it with the orchestrator.

### 2. The Tool Pattern
Agents do not implement complex logic directly. They use atomic `Tools` (e.g., `ELATool`, `CNASScraperTool`). This allows agents to switch tools dynamically (e.g., falling back from Tesseract to Gemini if OCR confidence is low).

### 3. Stateless Orchestration
The `AgentOrchestrator` is stateless. All state for a single verification session is maintained in an `AgentContext` object, which is passed between agents. This ensures thread-safety and allows for easy auditing.

### 4. Dependency Injection & Configuration
We use `Pydantic Settings` for configuration, ensuring that environment variables are validated at startup. Global resources like the `BrowserPool` are managed via FastAPI lifespans.
