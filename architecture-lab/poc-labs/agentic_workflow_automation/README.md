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
    participant Orch as Orchestrator (Controller)
    participant Planner as Task Planner (LLM)
    participant SS as State Store (Memory)
    participant Adapters as System Adapters (Tools)
    participant Policy as Guardrails (Safety)

    User->>Orch: "Book PTO for Friday"
    
    Note over Orch, SS: Phase 1: Context Retrieval
    Orch->>SS: fetch_session_history()
    SS-->>Orch: Context(User Preferences/History)

    Note over Orch, Planner: Phase 2: Iterative Planning
    Orch->>Planner: generate_plan(Intent, Context)
    Planner-->>Orch: Plan: [Task A, Task B]
    
    Orch->>Policy: validate_safety(Plan)
    Policy-->>Orch: Approval: True

    Note over Orch, Adapters: Phase 3: Execution Loop
    loop Every Task in Plan
        Orch->>Adapters: call_tool(args)
        Adapters-->>Orch: Result (Data or Error)
        
        alt is Error?
            Orch->>Planner: report_error(Error)
            Planner-->>Orch: Updated_Plan (Self-Correction)
        else is Success?
            Orch->>SS: save_checkpoint(Current_State)
        end
    end

    Note over Orch, User: Phase 4: Final Output
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

## ExecutionEngine Flow

This diagram shows the flow of execution for the `ExecutionEngine.run()` method, including action execution, rollback, and self-correction via `_replan_on_failure`.

```mermaid
flowchart TD
    %% -------------------------------
    %% Swimlanes / Subgraphs
    %% -------------------------------
    subgraph EX["Execution"]
        A["Start: run(plan, session_id)"] --> B{"More actions?"}
        B -- No --> Z["Return True"]
        B -- Yes --> C["Scrub action params (_scrubber.scrub_data)"]
        C --> E["_save_state(EXECUTING)"]
        E --> F{"Adapter exists?"}
        F -- Yes --> I{"Action supported?"}
        I -- Yes --> J["_execute_action_with_recovery"]
        J --> K{"Action succeeded?"}
        K -- Yes --> M["_save_state(PROPOSED)"]
        M --> B
        I -- No --> G["_fail_fast: Audit ACTION_FAILED + rollback"]
        F -- No --> G
    end

    subgraph AU["Audit"]
        D["Audit: ACTION_STARTED"]
        L["Audit: WorkflowState.PROPOSED"]
        N["Audit: WorkflowState.REJECTED + error details"]
        X["Audit: ACTION_FAILED (unexpected exception)"]
        S["Audit: PLAN_REPAIRED"]
        U["Audit: PLAN_UNRECOVERABLE"]
    end

    subgraph RB["Rollback"]
        O["_save_state(REJECTED)"]
        P["Rollback up to failed step"]
    end

    subgraph RC["Recovery / Replan"]
        Q["_replan_on_failure(failed_action, decision)"]
        R{"Repair plan returned?"}
        T["Re-run repaired plan"]
    end

    %% -------------------------------
    %% Connections between lanes
    %% -------------------------------
    C --> D
    D --> E

    J -- Failure(ActionFailure) --> N
    N --> O
    O --> P
    P --> Q
    Q --> R

    R -- Yes --> S
    S --> T
    T --> Z

    R -- No --> U
    U --> V["Return False"]

    J -- Unexpected Exception --> X
    X --> Y["Raise exception"]

```

## Getting Started

### Prerequisites

* Python 3.9+
* `pip install -r requirements.txt`

### Running the POC

```bash
python main.py

```
