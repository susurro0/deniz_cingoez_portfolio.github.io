from __future__ import annotations

import uuid
from time import perf_counter
from typing import Dict

from finops_llm_router.guardrails.guardrails import Guardrails
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.models.fin_obs_response import FinObsResponse
from finops_llm_router.orchestrator.strategy import RoutingStrategy
from finops_llm_router.providers.base_provider import BaseProvider
from finops_llm_router.providers.openai_provider import OpenAIProvider
from finops_llm_router.telemetry.collector import TelemetryCollector


class FinObsLLMOrchestrator:
    def __init__(
        self,
            guardrails: Guardrails,
            providers: Dict[str, BaseProvider],
            strategy: RoutingStrategy,
            telemetry: TelemetryCollector
    ):
        self.providers = providers
        self.guardrails = guardrails
        self.strategy = strategy
        self.telemetry = telemetry

    async def handle(self, req: FinObsRequest) -> FinObsResponse:
        # 1. Guardrails
        if not self.guardrails.validate(req.prompt):
            raise ValueError("Guardrail check failed")

        # 2. Strategy-based routing
        provider, model_name = self.strategy.select(req, self.providers)

        # 3. Execute request + measure latency
        start_time = perf_counter()
        llm_result = await provider.send_request(
            prompt=req.prompt,
            model=model_name,
        )
        latency_ms = (perf_counter() - start_time) * 1000

        # llm_result is assumed to be a unified internal response
        # Example:
        # {
        #   "content": "...",
        #   "usage": {"input_tokens": 120, "output_tokens": 340},
        #   "cost_estimated": 0.0042
        # }

        # 4. Async telemetry (non-blocking FinOps heartbeat)
        await self.telemetry.capture(
            request_id=req.id,
            provider=provider.name,
            model=model_name,
            usage=llm_result["usage"],
            cost_estimated=llm_result["cost_estimated"],
            latency_ms=latency_ms,
        )

        # 5. Unified FinOps response
        return FinObsResponse(
            id=str(uuid.uuid4()),
            content=llm_result["content"],
            model_used=model_name,
            provider=provider.name,
            usage=llm_result["usage"],
            cost_estimated=llm_result["cost_estimated"],
            latency_ms=latency_ms,
        )

    def list_providers(self):
        return list(self.providers.keys())
