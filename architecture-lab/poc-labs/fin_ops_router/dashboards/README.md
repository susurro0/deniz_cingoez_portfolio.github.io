# FinOps LLM Router – Telemetry Dashboard

## Overview

The FinOps LLM Router Dashboard provides visibility into **cost, performance, and routing decisions** made by the LLM orchestration layer.

It visualizes telemetry captured asynchronously during LLM request execution, enabling teams to:

* Track **LLM spend over time**
* Compare **providers and models**
* Understand **routing strategy decisions**
* Identify **latency bottlenecks**
* Demonstrate **FinOps and operational governance**

This dashboard is designed as a **Proof of Concept (POC)** and intentionally favors clarity and insight over production complexity, while mirroring real-world operational patterns.

---

## Objectives

The dashboard answers the following executive-level questions:

* How much are we spending on LLMs?
* Which providers and models are being used?
* Are cost-first vs performance-first strategies working as expected?
* What is the latency impact of routing decisions?
* How resilient is the system under provider failure?
* How does spend and performance change across datasets or environments?

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

* **Non-blocking telemetry** (no impact to request latency)
* **Local-first storage** using DuckDB
* **SQL-based analytics**
* **Minimal infrastructure**
* **Pluggable telemetry sources** (multiple DuckDB files supported)

---

## Telemetry Schema

The dashboard reads from a DuckDB database containing structured LLM execution telemetry.

### Canonical Schema

| Column         | Type      | Description                           |
| -------------- | --------- | ------------------------------------- |
| timestamp      | TIMESTAMP | Time of request execution             |
| request_id     | STRING    | Unique request identifier             |
| strategy       | STRING    | Routing strategy (cost / performance) |
| provider       | STRING    | Selected LLM provider                 |
| model          | STRING    | Selected model                        |
| usage_input    | INTEGER   | Tokens sent to the model              |
| usage_output   | INTEGER   | Tokens returned                       |
| cost_estimated | DOUBLE    | Estimated cost in USD                 |
| latency_ms     | DOUBLE    | End-to-end request latency            |

> **Note**
> The dashboard is **schema-resilient by design**.
> If certain telemetry fields (for example token counts) are missing, the dashboard degrades gracefully without failing.

This reflects real-world observability constraints where telemetry is often **best-effort**, not guaranteed.

---

## Dashboard Views

The dashboard includes the following core visualizations:

1. **Total LLM Spend**
2. **Spend by Model**
3. **Latency Trends Over Time**
4. **Request Volume by Routing Strategy**
5. **Detailed Telemetry Table**

These views are intentionally limited to maintain clarity and executive readability.

---

## Running the Dashboard

### Prerequisites

```bash
pip install duckdb streamlit pandas
```

---

## Start the Dashboard

From the `dashboards/` directory:

```bash
cd dashboards
streamlit run dashboard.py
```

---

## Telemetry Sources

The dashboard supports **runtime selection of DuckDB telemetry files** via the UI, allowing seamless switching between datasets.

### Default: Seeded Test Telemetry

By default, the dashboard loads:

```
dashboards/telemetry.duckdb
```

This file is created by running:

```bash
python seed_telemetry.py
```

The seed script generates **randomized test telemetry** and is intended for:

* Local development
* UI exploration
* Portfolio demonstrations

---

### Using Real Router Telemetry

To visualize **real LLM router telemetry**:

1. Run the `fin_ops_router` application from the project root so it emits telemetry
2. In the dashboard UI, update the **DuckDB file path** to point to:

```
fin_ops_router/telemetry.duckdb
```

The dashboard reloads immediately using the selected dataset.

> **Note**
> No code changes are required to switch between **synthetic** and **real** telemetry sources.

---

## Demo Flow

For a complete demonstration:

1. Run LLM requests using:

   * Cost-first routing
   * Performance-first routing
   * Simulated provider failure
2. Open the dashboard
3. Walk through:

   * Cost differences by model
   * Latency tradeoffs
   * Strategy effectiveness
   * Failover behavior

This flow demonstrates **FinOps discipline, operational resilience, and architectural intent**.

---

## Future Enhancements

* Real-time streaming telemetry
* Budget alerts and spend thresholds
* Per-team or per-project attribution
* Integration with PostgreSQL or cloud warehouses
* Governance metrics (guardrail violations)
* Telemetry schema versioning

---

## Why This Matters

This dashboard transforms the LLM router from a technical component into a **decision-support system**.

It enables:

* Finance teams to track and forecast spend
* Engineering leaders to assess performance tradeoffs
* Executives to understand ROI, risk, and operational maturity

This is the core of **LLMOps + FinOps convergence**.
