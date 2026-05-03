# Visual System Representation

This document provides a high-level visual perspective of the system's integration within the broader ecosystem.

## Ecosystem Block Diagram

```mermaid
graph LR
    User([End User/Doctor]) -->|Uploads Docs| Dashboard[Frontend Dashboard]:::frontend
    Dashboard -->|API Request| AIService[AI Verification Service]:::backend
    
    subgraph AIService [AI Verification Service]
        Orch[Orchestrator]:::core
        Agents[7 Specialized Agents]:::core
        Pool[Browser Pool]:::resource
    end
    
    AIService -->|LLM Reasoning| Gemini[Google Gemini AI]:::ai
    AIService -->|OCR| Tesseract[Tesseract/Vision]:::ai
    AIService -->|Web Automation| CNAS[CNAS Government Portal]:::gov
    
    AIService -->|SSE Events| Dashboard:::frontend

    %% Styles
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#01579b
    classDef backend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#7b1fa2
    classDef core fill:#ffffff,stroke:#424242,stroke-width:2px,color:#424242
    classDef resource fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100
    classDef ai fill:#ede7f6,stroke:#4527a0,stroke-width:2px,color:#4527a0
    classDef gov fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#2e7d32
```

## Internal Data Model (Mindmap)

The system uses a **Centralized Shared State** model. This is more resilient than a chain-link pipeline because agents can revisit previous decisions if new information becomes available.

```mermaid
mindmap
  root((<b>Verification Engine</b>))
    (<b>Agent Context</b>)
      ::icon(fa fa-database)
      Results
      Reasoning Trace
      Binary Artifacts
    (<b>Agentic Core</b>)
      ::icon(fa fa-brain)
      Classification
      OCR Extraction
      Forgery Detection
      Scraping Logic
    (<b>External Tools</b>)
      ::icon(fa fa-cloud)
      Gemini Flash
      Playwright Pool
      Tesseract OCR
```

## Why this Visualization Matters
This structure proves that the system is **decoupled**. We can swap out the OCR tool or the government portal URL without ever changing the Frontend logic or the core Orchestrator. It is built for the long-term evolution of the Algerian digital economy.
