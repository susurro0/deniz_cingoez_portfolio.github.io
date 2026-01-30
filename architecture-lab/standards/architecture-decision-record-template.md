# ADR-[000]: [Short Title of the Decision]

* **Status:** [Proposed / Accepted / Superseded / Deprecated]
* **Owner:** [Engineer Name]
* **Deciders:** [List of Stakeholders, e.g., Senior EM, Staff Engineer, Product Lead]
* **Date:** YYYY-MM-DD

## Context and Problem Statement
What is the business or technical driver for this change? 
*Example: Our current batch scoring process is taking 4 hours, which violates our Finance SLA of 1 hour.*

## Decision Drivers
* Cost efficiency (Azure compute spend)
* Auditability (Financial compliance)
* Developer velocity (How fast can the squad learn this?)

## Considered Options
1.  [Option 1: e.g., Keep legacy Spark jobs]
2.  [Option 2: e.g., Migrate to Azure Machine Learning Managed Endpoints]

## Decision Outcome
Chosen Option: **[Option #]**

### Consequences
* **Positive:** [e.g., Reduces latency to 15 minutes.]
* **Negative:** [e.g., Higher upfront cost in infrastructure-as-code setup.]
* **Risks:** [e.g., Team needs training on the new Azure ML SDK.]

---
## Validation Plan
How will we know this worked? (e.g., Load testing at 2x current volume).