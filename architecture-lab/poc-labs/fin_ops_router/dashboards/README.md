# FinOps LLM Router – Telemetry Dashboard

## Overview

The FinOps LLM Router Dashboard provides visibility into **cost, performance, and routing decisions** made by the LLM orchestration layer.

It visualizes telemetry captured asynchronously during LLM request execution, enabling teams to:

- Track **LLM spend over time**
- Compare **providers and models**
- Understand **routing strategy decisions**
- Identify **latency bottlenecks**
- Demonstrate **FinOps and operational governance**

This dashboard is designed as a **Proof of Concept (POC)** and intentionally favors clarity and insight over production complexity.

---

## Objectives

The dashboard answers the following executive-level questions:

- How much are we spending on LLMs?
- Which providers and models are being used?
- Are cost-first vs performance-first strategies working as expected?
- What is the latency impact of routing decisions?
- How resilient is the system under provider failure?

---

## Architecture

```mermaid
flowchart TD
    A[LLM Orchestrator] --> B[TelemetryCollector<br/>(async, non-blocking)]
    B --> C[DuckDB<br/>(structured telemetry sink)]
    C --> D[Streamlit Dashboard]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bfb,stroke:#333,stroke-width:2px
    style D fill:#ffb,stroke:#333,stroke-width:2px
```

### Key Characteristics

- **Non-blocking telemetry** (no impact to request latency)
- **Local-first storage** using DuckDB
- **SQL-based analytics**
- **Minimal infrastructure**

---

## Telemetry Schema

The dashboard reads from a DuckDB database with the following schema:

| Column | Type | Description |
|------|------|-------------|
| timestamp | TIMESTAMP | Time of request execution |
| request_id | STRING | Unique request identifier |
| strategy | STRING | Routing strategy (cost / performance) |
| provider | STRING | Selected LLM provider |
| model | STRING | Selected model |
| input_tokens | INTEGER | Tokens sent to the model |
| output_tokens | INTEGER | Tokens returned |
| cost_estimated | DOUBLE | Estimated cost in USD |
| latency_ms | DOUBLE | End-to-end request latency |

---

## Dashboard Views

The dashboard includes the following core visualizations:

1. **Total LLM Spend**
2. **Spend by Provider**
3. **Latency by Provider & Model**
4. **Request Volume by Routing Strategy**
5. **Provider Failure / Failover Events**

These views are intentionally limited to maintain clarity and executive readability.

---

## Running the Dashboard

### Prerequisites

```bash
pip install duckdb streamlit pandas
````

### Start the Dashboard

```bash
streamlit run dashboard/app.py
```

By default, the dashboard reads from:

```
telemetry.duckdb
```

This file is created automatically by the TelemetryCollector when requests are processed.

---

## Demo Flow (Recommended)

For a complete demonstration:

1. Run a script that issues LLM requests using:

   * Cost-first routing
   * Performance-first routing
   * Simulated provider failure
2. Open the dashboard
3. Walk through:

   * Cost differences
   * Latency tradeoffs
   * Failover behavior

This flow demonstrates **FinOps discipline, operational resilience, and architectural intent**.

---

## Future Enhancements

* Real-time streaming telemetry
* Budget alerts and thresholds
* Per-team or per-project attribution
* Integration with PostgreSQL or cloud warehouses
* Governance metrics (guardrail violations)

---

## Why This Matters

This dashboard transforms the LLM router from a technical component into a **decision-support system**.

It enables:

* Finance teams to track spend
* Engineering leaders to assess performance
* Executives to understand ROI and risk

This is the core of **LLMOps + FinOps convergence**.


