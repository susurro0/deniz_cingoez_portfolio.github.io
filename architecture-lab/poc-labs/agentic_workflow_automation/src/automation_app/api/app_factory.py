# automation_app/api/app_factory.py

from fastapi import FastAPI

from automation_app.adapters.msgraph_adapter import MSGraphAdapter
from automation_app.adapters.workday_adapter import WorkdayAdapter
from automation_app.api.routes.orchestrator_routes import OrchestratorRoutes
from automation_app.engines.execution_engine import ExecutionEngine
from automation_app.engines.intent_classifier import IntentClassifier
from automation_app.engines.policy_engine import PolicyEngine
from automation_app.engines.task_planner import TaskPlanner
from automation_app.orchestrator import AgenticOrchestrator
from automation_app.store.state_store import StateStore


class AppFactory:
    def __init__(self):
        self.app = FastAPI(title="Agentic Workflow Orchestrator")
        self._setup_dependencies()
        self._register_routes()

    def _setup_dependencies(self):
        adapters = {
            "Workday": WorkdayAdapter(),
            "MSGraph": MSGraphAdapter()
        }

        self.orchestrator = AgenticOrchestrator(
            classifier=IntentClassifier(),
            planner=TaskPlanner(),
            policy_engine=PolicyEngine(),
            executor=ExecutionEngine(adapters),
            state_store=StateStore()
        )

    def _register_routes(self):
        routes = OrchestratorRoutes(self.orchestrator)
        self.app.include_router(routes.router)

    def get_app(self) -> FastAPI:
        return self.app
