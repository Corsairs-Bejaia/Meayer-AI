# Visual Representation of the System

This document provides a simplified visual view of how the system sits within the broader ecosystem.

## High-Level Block Diagram

```mermaid
graph LR
    User([End User]) -->|Uploads Docs| Dashboard[Frontend Dashboard]
    Dashboard -->|API Request| AIService[AI Verification Service]
    
    subgraph AIService [AI Verification Service]
        Orch[Orchestrator]
        Agents[7 Specialized Agents]
        Pool[Browser Pool]
    end
    
    AIService -->|LLM Reasoning| Gemini[Google Gemini AI]
    AIService -->|OCR| Paddle[PaddleOCR / Tesseract]
    AIService -->|Web Automation| CNAS[CNAS Government Portal]
    
    AIService -->|Real-time Updates| Dashboard
```

## Internal Interaction Model

The system uses a **Centralized Shared State** model. This is more resilient than a chain-link pipeline because agents can revisit previous decisions if new information becomes available.

```mermaid
mindmap
  root((Orchestrator))
    AgentContext
      Results
      Trace
      Artifacts
    Agents
      Classification
      OCR
      Extraction
      Authenticity
      Consistency
      Scraping
      Scoring
    External
      Gemini API
      Playwright Browsers
      OS Tesseract
```
