## Onboarding & Configuration

This section helps new developers quickly get up to speed with the FinOps LLM Router and Telemetry Engine.

### 1. Onboarding Guide

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/fin_ops_router.git
   cd fin_ops_router
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Seed telemetry data for testing:**

   ```bash
   python dashboards/seed_telemetry.py
   ```

4. **Run the dashboard (optional):**

For full instructions on running and interacting with the Streamlit dashboard, see [`dashboards/README.md`](dashboards/README.md).


5. **Start the FastAPI service:**

   ```bash
   uvicorn src.main:app --reload
   ```

---

### 2. Configuration Examples

Configuration files live in `src/finops_llm_router/config/` and allow you to:

* Define default routing strategies (cost-first, performance-first).
* Configure guardrails and policy enforcement.
* Add new LLM providers or models.

Example (JSON):

```json
{
  "providers": ["openai", "anthropic", "bedrock"],
  "default_strategy": "cost",
  "max_cost_per_request": 0.05,
  "guardrails": ["no_sensitive_data", "no_blocked_terms"]
}
```

---

### 3. Available API Endpoints

| Method | Path            | Description                                                                                      |
| ------ | --------------- | ------------------------------------------------------------------------------------------------ |
| POST   | `/v1/llm`       | Submit a request to the LLM router. Accepts `FinObsRequest` JSON, returns `FinObsResponse` JSON. |
| GET    | `/health`       | Health check. Returns `{"status": "ok", "service": "finops-llm-router"}`.                        |
| GET    | `/v1/providers` | Lists all available LLM providers configured in the orchestrator.                                |
| GET    | `/metrics`      | Returns basic telemetry metrics: total requests, estimated cost, average latency.                |

**Example Request (`FinObsRequest`):**

```json
{
  "id": "uuid",
  "prompt": "Summarize the financial report",
  "task_type": "general",
  "priority": "cost",
  "metadata": {"team": "finance"}
}
```

**Example Response (`FinObsResponse`):**

```json
{
  "id": "uuid",
  "content": "Summary of financial report...",
  "model_used": "GPT-4o-mini",
  "provider": "openai",
  "usage": {"input_tokens": 50, "output_tokens": 25},
  "cost_estimated": 0.0015,
  "latency_ms": 123.4
}
```

