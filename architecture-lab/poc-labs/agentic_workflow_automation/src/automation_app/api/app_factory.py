import contextlib
from contextlib import asynccontextmanager
import asyncio
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
        self.app = FastAPI(
            title="Agentic Workflow Orchestrator",
            lifespan=self.lifespan
        )
        self.orchestrator = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
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

        self._register_routes()

        async def run_cleanup():
            while True:
                await self.orchestrator.cleanup_stale_proposals()
                await asyncio.sleep(60)

        cleanup_task = asyncio.create_task(run_cleanup())

        try:
            yield
        finally:
            # --- Teardown Phase ---
            cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cleanup_task
            # await state_store.close_connection()
            pass

    def _register_routes(self):
        routes = OrchestratorRoutes(self.orchestrator)
        self.app.include_router(routes.router)

    def get_app(self) -> FastAPI:
        return self.app


app_factory = AppFactory()
app = app_factory.get_app()
