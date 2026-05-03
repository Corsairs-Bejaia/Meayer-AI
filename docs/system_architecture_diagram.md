# System Architecture Diagram

This diagram represents the flow of data through the 7-agent pipeline.

```mermaid
graph TD
    %% Input
    Input[Document Images] --> O[Agent Orchestrator]

    %% Shared Context
    O <--> Context[(Agent Context)]

    %% Parallel Execution
    subgraph Parallel Phase
        A1[Classifier Agent]
        A2[OCR Agent]
        A4[Authenticity Agent]
    end
    
    O --> A1 & A2 & A4
    A1 & A2 & A4 <--> Context

    %% Sequential Reasoning
    subgraph Sequential Phase
        A3[Extraction Agent]
        A5[Consistency Agent]
        A7[Scraping Agent]
        A6[Scoring Agent]
        A8[Report Agent]
    end

    A1 -.-> A3
    A2 -.-> A3
    
    O --> A3
    A3 --> A5
    A5 --> A7
    A7 --> A6
    A6 --> A8

    A3 & A5 & A7 & A6 & A8 <--> Context

    %% Output
    A8 --> Output[Final Decision & JSON Report]
```

## Phase Breakdown

- **Parallel Phase**: I/O-bound and compute-heavy tasks that don't depend on each other (Classification, OCR, Forgery Detection).
- **Sequential Phase**: Reasoning tasks where results from previous agents are required (e.g., Scraping needs the ID number extracted by the Extraction Agent).
