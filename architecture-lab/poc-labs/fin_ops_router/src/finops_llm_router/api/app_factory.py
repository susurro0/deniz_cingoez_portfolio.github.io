import contextlib
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI

from finops_llm_router.api.routes.fin_obs_routes import FinObsRoutes
from finops_llm_router.guardrails.guardrails import Guardrails
from finops_llm_router.orchestrator.cost_first_strategy import CostFirstStrategy
from finops_llm_router.orchestrator.finobs_llm_orchestrator import FinObsLLMOrchestrator
from finops_llm_router.orchestrator.performance_first_strategy import PerformanceFirstStrategy
from finops_llm_router.providers.anthropic_provider import AnthropicProvider
from finops_llm_router.providers.openai_provider import OpenAIProvider
from finops_llm_router.telemetry.collector import TelemetryCollector


class AppFactory:
    def __init__(self):
        self.app = FastAPI(
            title="FinOps LLM Router POC",
            lifespan=self.lifespan
        )
        self.orchestrator = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        self.providers = {
            "openai": OpenAIProvider(api_key="..."),
            "anthropic": AnthropicProvider(api_key="..."),
        }
        self.orchestrator = FinObsLLMOrchestrator(
            guardrails=Guardrails(),
            providers=self.providers,
            telemetry=TelemetryCollector(),

        )

        self._register_routes()

        yield

    def _register_routes(self):
        routes = FinObsRoutes(self.orchestrator)
        self.app.include_router(routes.router)

    def get_app(self) -> FastAPI:
        return self.app


app_factory = AppFactory()
app = app_factory.get_app()
