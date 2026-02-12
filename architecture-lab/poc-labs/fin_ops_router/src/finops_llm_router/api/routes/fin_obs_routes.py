from http.client import HTTPException

from fastapi import APIRouter

from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.models.fin_obs_response import FinObsResponse
from finops_llm_router.orchestrator.finobs_llm_orchestrator import FinObsLLMOrchestrator


class FinObsRoutes:
    def __init__(self, orchestrator: FinObsLLMOrchestrator):
        self. orchestrator = orchestrator
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self):
        @self.router.post(
            "/v1/llm",
            response_model=FinObsResponse
        )
        async def llm_request(req: FinObsRequest):
            return await self.orchestrator.handle(req)

        @self.router.get("/health")
        def health():
            return {
                "status": "ok",
                "service": "finops-llm-router"
            }

        @self.router.get("/v1/providers")
        def providers():
            return {
                "providers": self.orchestrator.list_providers()
            }

        @self.router.get("/metrics")
        def metrics():
            return {
                "requests_total": 0,
                "cost_estimate_usd": 0.0,
                "avg_latency_ms": 0
            }