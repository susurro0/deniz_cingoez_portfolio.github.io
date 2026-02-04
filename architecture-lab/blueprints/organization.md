# Organizational Operating Model & Leadership Philosophy

> **The Goal:** To build a "Team of Teams" that is autonomous, auditable, and architecturally aligned. I measure my success by the velocity of the teams I lead and the career growth of the engineers within them.

## Core Principles
1. **Paved Paths over Gatekeeping:** We build tools that make the right way the easiest way.
2. **Intentional Debt:** We treat technical debt as a financial instrument—useful for speed, but dangerous if the interest isn't managed.
3. **Auditability as a Feature:** Especially in Finance/Insurance, knowing "why" is as important as "what."


## Handling Technical Debt Across Multiple Squads

I treat technical debt as a portfolio problem, not a team failure. Across multiple squads, debt is inevitable when teams are shipping real value, so the goal isn’t elimination — it’s visibility and intentional tradeoffs. We track debt explicitly through ADRs, platform backlogs, and post-incident reviews, and we make debt conversations part of quarterly planning rather than something teams apologize for. When debt begins to impact velocity, reliability, or onboarding, it becomes a shared priority between product and engineering leadership, not something engineers are expected to “clean up on the side.”

At the platform level, I bias toward paved paths and opinionated defaults to prevent debt from multiplying across teams. If five squads are solving the same problem five different ways, that’s organizational debt, and it’s my responsibility to consolidate it. This often means investing early in shared libraries, templates, or services so individual teams can move faster without carrying long-term maintenance risk.

---

## Definition of Ready for Production ML Models

Before a model is allowed into the production subgraph, the bar is intentionally higher than “it works.” A model is considered ready only when ownership, lineage, and failure modes are clearly defined. That means the training dataset is versioned, features come from an approved feature store, and the model is registered with traceability back to its source data. If we can’t explain where the data came from or reproduce the model, it doesn’t ship.

Operational readiness matters just as much as model quality. The inference service must have defined SLAs, monitoring for drift and performance, and a rollback strategy that doesn’t require heroics. I’m less interested in perfect accuracy than I am in predictable behavior under real-world conditions. If a model degrades gracefully and fails safely, it’s ready. If it doesn’t, it stays out of production.

---

## Mentoring Lead Engineers to Own Subgraphs

I mentor Lead Engineers by giving them real ownership, not just more meetings. Each Lead is responsible for a specific subgraph — whether that’s training pipelines, inference, feature stores, or governance — and is expected to think beyond their immediate team. That ownership includes technical direction, documentation quality, and being the escalation point when things go wrong.

My role is to help Leads zoom out: understanding how their subgraph impacts other teams, where abstractions are leaking, and when it’s time to simplify. We regularly review architecture decisions together, especially the ones that didn’t age well. Over time, the goal is for Leads to operate with the same platform-first mindset I expect of myself — designing systems that make the right thing the easy thing for everyone else.
