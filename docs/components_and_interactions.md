# Components and Their Interactions

This document details how the different software components interact to fulfill a verification request.

## Component Overview

| Component | Responsibility | Interaction Pattern |
| :--- | :--- | :--- |
| **AgentOrchestrator** | Orchestrates the full pipeline lifecycle. | **Caller**: Invokes all agents. |
| **AgentContext** | Shared data store for a single request. | **State Store**: Read/Write by all agents. |
| **BaseAgent** | Interface for all agents. | **Contract**: Defines the `run()` method. |
| **BaseTool** | Atomic unit of work (e.g., OCR, Image manipulation). | **Worker**: Executed by agents. |
| **BrowserPool** | Manages a pool of headless Playwright instances. | **Singleton**: Used primarily by ScrapingAgent. |

## Interaction Sequence

1.  **Request Initiation**: FastAPI router receives a request and instantiates an `AgentOrchestrator`.
2.  **Context Creation**: The Orchestrator creates an `AgentContext` and attaches the raw document images.
3.  **Parallel Execution**: 
    - The `Classifier` writes the `doc_type` to the Context.
    - `Authenticity` writes the `forgery_score` to the Context.
    - `OCR` writes the raw `text` to the Context.
4.  **Dependent Reasoning**:
    - The `ExtractionAgent` waits for the `OCR` result, then reads the text and writes structured fields back to the Context.
    - The `ConsistencyAgent` reads fields from all documents to check for name/ID mismatches.
5.  **External Automation**:
    - The `ScrapingAgent` checks if any CNAS documents exist. If so, it requests a browser from the `BrowserPool` and performs the live check.
6.  **Final Scoring**:
    - The `ScoringAgent` reads all results from the Context and applies weighted logic to produce a final score.
