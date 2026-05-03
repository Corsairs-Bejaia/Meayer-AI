# Components and Interactions

This document details how the software components collaborate to fulfill a doctor verification request.

## Interaction Sequence

```mermaid
sequenceDiagram
    autonumber
    participant U as User/API
    participant O as Orchestrator
    participant C as Agent Context
    participant A as Specialist Agents
    participant T as Tools (OCR, Vision)
    participant B as Browser Pool

    U->>O: Submit Documents
    O->>C: Initialize Request Context
    
    rect rgb(240, 248, 255)
    Note over O, A: Parallel Phase
    O->>A: Trigger Classifier, OCR, Authenticity
    A->>T: Execute Atomic Tools
    T-->>A: Raw Data (Text, Scores)
    A->>C: Write Findings
    end

    rect rgb(245, 245, 2DC)
    Note over O, A: Sequential Reasoning
    O->>A: Trigger Extraction & Consistency
    A->>C: Read Raw Data
    A->>C: Write Structured Results
    end

    rect rgb(230, 255, 230)
    Note over A, B: External Verification
    A->>B: Request Browser Context
    B->>A: Browser Ready
    A->>A: Perform Live Gov Scraping
    A->>C: Write Portal Status
    end

    O->>C: Final Scoring Calculation
    C-->>O: Trust Decision
    O-->>U: JSON Report + Verification Trace
```

## Component Responsibility Matrix

| Component | Responsibility | Interaction Pattern |
| :--- | :--- | :--- |
| **AgentOrchestrator** | Orchestrates the full pipeline lifecycle and manages thread safety. | **Caller**: Primary entry point. |
| **AgentContext** | The ephemeral shared data store for a single verification session. | **State Store**: Centralized memory. |
| **BaseAgent** | Core logic interface for all specialized agents (OCR, Scraping, etc.). | **Contract**: Domain logic executor. |
| **BaseTool** | Atomic unit of work (e.g., Tesseract OCR, Gemini Vision, ELA analysis). | **Worker**: Executed by agents. |
| **BrowserPool** | Manages a thread-safe pool of headless Playwright instances. | **Resource**: Managed service. |
