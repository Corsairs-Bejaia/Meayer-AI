# System Architecture

The AI Verification Service is built on an **Agentic Orchestration** model. Instead of a rigid linear pipeline, the system uses a central orchestrator to manage specialized agents that can adapt to the input they receive.

## High-Level Workflow

1.  **Ingestion**: Images are received via the FastAPI `/api/pipeline` endpoint.
2.  **Parallel Analysis**: The `Classifier`, `OCR`, and `Authenticity` agents run concurrently to minimize latency.
3.  **Contextual reasoning**: Once the document type and text are known, the `ExtractionAgent` pulls specific fields.
4.  **Verification**: The `ConsistencyAgent` checks for mismatches across documents, and the `ScrapingAgent` performs live government portal validation.
5.  **Final Judgment**: The `ScoringAgent` calculates a trust score and issues a decision.

## Key Concepts

### AgentContext
The "Source of Truth" for a verification request. It stores:
- Raw document data.
- Results from every agent.
- A "trace" of all tools executed (for auditing).

### Self-Correction
Agents can detect their own failures. For example, if `PaddleOCR` returns unreadable text, the `OCRAgent` will automatically retry using `Gemini Vision` with a specialized "repair" prompt.

### Layered Verification
We use a 6-layer verification model (Identity, Academic, Standing, etc.) to ensure that the user has submitted all required proof before issuing an "Approved" status.
