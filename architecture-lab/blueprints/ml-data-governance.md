flowchart LR
    subgraph Finance_Data_Sources["Finance & Enterprise Data Sources"]
        A1[Policy Systems]
        A2[Claims Systems]
        A3[Billing & GL]
    end

    subgraph Data_Platform["Enterprise Data Platform"]
        B1[Raw Data Lake]
        B2[Curated Analytics Tables]
        B3[Feature Store]
    end

    subgraph ML_Training["ML Training (Ephemeral)"]
        C1[Training Job]
        C2[Model Artifacts]
        C3[Dataset Version]
    end

    subgraph Model_Governance["Model Registry & Governance"]
        D1[Model Registry]
        D2[Approval Workflow]
        D3[Lineage & Audit Logs]
    end

    subgraph Production_Inference["Production Inference Platform"]
        E1[Inference Service]
        E2[API / Batch Scoring]
        E3[Monitoring & Drift Detection]
    end

    subgraph Cost_Control["Cost Controls"]
        F1[Auto-Scale Up]
        F2[Auto-Shutdown After Training]
    end

    %% Data Flow
    A1 --> B1
    A2 --> B1
    A3 --> B1

    B1 --> B2
    B2 --> B3

    %% Separation of Concerns
    B3 -->|Features| C1
    C1 --> C2
    C1 --> C3

    %% Governance & Auditability
    C2 --> D1
    C3 --> D1
    D1 --> D2
    D1 --> D3

    %% Promotion to Production
    D2 -->|Approved Model| E1
    E1 --> E2
    E1 --> E3

    %% Cost Control
    C1 --> F1
    C1 --> F2
