# System Architecture Diagram

This diagram represents the logical and technical flow of data through the 7-agent verification pipeline.

```mermaid
graph TD
    %% Input
    Input[Document Images]:::input --> O[Agent Orchestrator]:::core

    %% Shared Context
    O <--> Context[(Agent Context)]:::context

    %% Parallel Execution
    subgraph ParallelPhase [Parallel Analysis]
        direction LR
        A1[Classifier Agent]:::agent
        A2[OCR Agent]:::agent
        A4[Authenticity Agent]:::agent
    end
    
    O --> ParallelPhase
    ParallelPhase <--> Context

    %% Sequential Reasoning
    subgraph SequentialPhase [Sequential Reasoning]
        direction TB
        A3[Extraction Agent]:::agent
        A5[Consistency Agent]:::agent
        A7[Scraping Agent]:::agent
        A6[Scoring Agent]:::agent
        A8[Report Agent]:::agent
    end

    ParallelPhase --> A3
    A3 --> A5
    A5 --> A7
    A7 --> A6
    A6 --> A8

    SequentialPhase <--> Context

    %% Output
    A8 --> Output[Final Decision & Report]:::output

    %% Styles
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#1565c0
    classDef core fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#7b1fa2
    classDef context fill:#fafafa,stroke:#424242,stroke-width:2px,color:#424242,stroke-dasharray: 5 5
    classDef agent fill:#ffffff,stroke:#37474f,stroke-width:2px,color:#37474f
    classDef output fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#2e7d32
```

## Phase Breakdown

### Parallel Analysis
I/O-bound and compute-heavy tasks that run concurrently to reduce total processing time. This phase focuses on raw data gathering:
* **Classification**: Identifying the document type.
* **OCR**: Extracting raw text layers.
* **Authenticity**: Running forensic forgery detection.

### Sequential Reasoning
Tasks that require cross-agent intelligence and dependent data:
* **Extraction**: Mapping text to specific medical fields.
* **Consistency**: Cross-referencing data points between documents.
* **Scraping**: Automated verification against live government portals (CNAS/CASNOS).
* **Scoring**: Final risk calculation and trust assignment.
