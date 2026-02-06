from contextlib import asynccontextmanager
from fastapi import FastAPI

from automation_app.adapters.msgraph_adapter import MSGraphAdapter
from automation_app.adapters.workday_adapter import WorkdayAdapter
from automation_app.api.routes.orchestrator_routes import OrchestratorRoutes
from automation_app.config.policies import POLICY_RULES
from automation_app.engines.execution_engine import ExecutionEngine
from automation_app.engines.intent_classifier import IntentClassifier
from automation_app.engines.policy_engine import PolicyEngine
from automation_app.engines.task_planner import TaskPlanner
from automation_app.orchestrator import AgenticOrchestrator
from automation_app.store.state_store import StateStore
from automation_app.utils.pii_scrubber import PIIScrubber


class AppFactory:
    def __init__(self):
        # We define the lifespan to handle async setup/teardown
        self.app = FastAPI(
            title="Agentic Workflow Orchestrator",
            lifespan=self.lifespan
        )
        self.orchestrator = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        Handles async setup and teardown of dependencies.
        """
        # --- Setup Phase ---
        # If your adapters or store need to connect to a DB/API, 
        # you can now 'await' those connections here.
        state_store = StateStore()

        adapters = {
            "Workday": WorkdayAdapter(),
            "MSGraph": MSGraphAdapter()
        }

        self.orchestrator = AgenticOrchestrator(
            classifier=IntentClassifier(),
            planner=TaskPlanner(),
            policy_engine=PolicyEngine(rules=POLICY_RULES),
            executor=ExecutionEngine(adapters),
            state_store=state_store,
            scrubber=PIIScrubber()
        )

        # Register routes now that orchestrator is ready
        self._register_routes()

        yield

        # --- Teardown Phase ---
        # await state_store.close_connection() 

    def _register_routes(self):
        # Ensure we only register once
        routes = OrchestratorRoutes(self.orchestrator)
        self.app.include_router(routes.router)

    def get_app(self) -> FastAPI:
        return self.app


# Create the instance
app_factory = AppFactory()
app = app_factory.get_app()