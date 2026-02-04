# POC: Agentic Workflow Automation

### Enterprise HR & Workspace Orchestration

## Problem Statement

In large enterprises, "Agentic AI" often fails because it is treated as a black box. Without **Human-in-the-Loop (HITL)** controls, **State Management**, and **Policy Enforcement**, autonomous agents represent a significant security and operational risk.

This POC demonstrates a structured orchestration layer that safely bridges LLM reasoning with protected Enterprise APIs (Workday, MS Graph).

---

## System Architecture

### Class Relationship Diagram

This POC uses an Object-Oriented approach to separate intent classification from execution, ensuring the system is "Open/Closed"—new adapters can be added without modifying the core logic.

```mermaid
classDiagram
    class AgenticOrchestrator {
        -IntentClassifier classifier
        -TaskPlanner planner
        -PolicyEngine policy_engine
        -ExecutionEngine executor
        -StateStore state
        +process_request(user_input: str)
    }

    class IntentClassifier {
        +classify(text: str) Intent
    }

    class TaskPlanner {
        -LLMClient llm
        +generate_plan(intent: Intent, state: dict) Plan
    }

    class PolicyEngine {
        +validate_plan(plan: Plan) bool
        +check_permissions(user_id: str, action: str) bool
    }

    class ExecutionEngine {
        -list adapters
        -AuditLogger logger
        +run(plan: Plan) bool
        +rollback(step_id: str)
    }

    class EnterpriseAdapter {
        <<interface>>
        +execute(action: str, params: dict) dict
    }

    class WorkdayAdapter {
        +get_pto_balance() float
        +book_time_off(dates: list)
    }

    class MSGraphAdapter {
        +check_calendar_availability(date: str) bool
        +create_event(details: dict)
    }

    class StateStore {
        -dict storage
        +save_context(session_id: str, data: dict)
        +get_context(session_id: str) dict
    }

    AgenticOrchestrator --> IntentClassifier
    AgenticOrchestrator --> TaskPlanner
    AgenticOrchestrator --> PolicyEngine
    AgenticOrchestrator --> ExecutionEngine
    ExecutionEngine --> EnterpriseAdapter
    EnterpriseAdapter <|-- WorkdayAdapter
    EnterpriseAdapter <|-- MSGraphAdapter
    ExecutionEngine --> StateStore
```

---

## Execution Flow

The following sequence highlights the **Authorization Gate**. The system will not call an Enterprise API until the user has confirmed the "Proposed Plan" and the Policy Engine has verified permissions.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Orch as Orchestrator
    participant IC as Intent Classifier
    participant SS as State Store
    participant Planner as Task Planner (LLM)
    participant Policy as Policy Engine
    participant Adapters as System Adapters

    User->>Orch: "Book PTO for Friday"
    
    Note over Orch, IC: Phase 1: Understanding
    Orch->>IC: classify(text)
    IC-->>Orch: Intent(type='PTO', entity='Friday')
    
    Orch->>SS: get_context(session_id)
    SS-->>Orch: {previous_context: None}

    Note over Orch, Planner: Phase 2: Reasoning
    Orch->>Planner: generate_plan(Intent, Context)
    Planner-->>Orch: Plan: [Check Calendar, Book Workday]
    
    Orch->>User: "I'll check your calendar and book PTO. Confirm?"
    User->>Orch: "Yes, go ahead."

    Note over Orch, Policy: Phase 3: Validation
    Orch->>Policy: validate_plan(Plan)
    Policy-->>Orch: bool(True)

    Note over Orch, Adapters: Phase 4: Execution
    Orch->>Adapters: execute(MSGraph, 'check_availability')
    Adapters-->>Orch: Status: Available
    Orch->>Adapters: execute(Workday, 'book_time_off')
    Adapters-->>Orch: Status: Success (Ref: 123)

    Note over Orch, SS: Phase 5: Persistence
    Orch->>SS: save_context(session_id, updated_state)
    Orch->>User: "Done! PTO is booked (Ref: 123)"
    
```

---

## Key Technical Features

* **Human-in-the-Loop (HITL):** A mandatory confirmation step between the *Reasoning* and *Execution* phases.
* **Identity Propagation:** Logic designed to carry user tokens through to adapters (mocked in this POC).
* **State Awareness:** The orchestrator maintains a `StateStore` to handle multi-turn conversations (e.g., "Wait, move it to Monday instead").
* **Policy-as-Code:** A dedicated engine that checks the generated plan against enterprise constraints before execution.

---

## Design Principles

* **Single Responsibility:** The Planner reasons, the Policy Engine validates, and the Adapters execute. No cross-contamination.
* **Fail-Fast:** If the Policy Engine rejects a plan, execution is halted before a single API call is made.
* **Audit-by-Design:** Every state transition in the `StateStore` is an immutable event, providing a natural audit trail.

--- 

## 📁 Project Structure
- `orchestrator.py`: Core logic and service coordination.
- `models/`: Dataclasses for `Intent`, `Plan`, and `Action`.
- `engines/`: Implementation of `TaskPlanner` and `PolicyEngine`.
- `adapters/`: Individual wrappers for Workday and MS Graph APIs.
- `store/`: State and context management.

---
## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* `pip install -r requirements.txt`

### Running the POC

```bash
python main.py

```
