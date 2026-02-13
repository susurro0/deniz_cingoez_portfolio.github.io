from __future__ import annotations

import uuid
from time import perf_counter
from typing import Dict

from finops_llm_router.guardrails.guardrails import Guardrails
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.models.fin_obs_response import FinObsResponse
from finops_llm_router.orchestrator.cost_first_strategy import CostFirstStrategy
from finops_llm_router.orchestrator.performance_first_strategy import PerformanceFirstStrategy
from finops_llm_router.orchestrator.strategy import RoutingStrategy
from finops_llm_router.providers.base_provider import BaseProvider
from finops_llm_router.providers.openai_provider import OpenAIProvider
from finops_llm_router.telemetry.collector import TelemetryCollector


class FinObsLLMOrchestrator:
    def __init__(
        self,
            guardrails: Guardrails,
            providers: Dict[str, BaseProvider],
            telemetry: TelemetryCollector
    ):
        self.providers = providers
        self.guardrails = guardrails
        self.telemetry = telemetry

        # Strategy registry
        self.strategies = {
            "cost": CostFirstStrategy(),
            "performance": PerformanceFirstStrategy(),
        }

    async def handle(self, req: FinObsRequest) -> FinObsResponse:
        # 1. Guardrails
        if not self.guardrails.validate(req.prompt):
            raise ValueError("Guardrail check failed")

        # 2. Select routing strategy (FIXED)
        strategy = self.strategies.get(req.priority.lower())
        if not strategy:
            raise ValueError(f"Unknown routing strategy: {req.priority}")

        provider, model_name = strategy.select(req, self.providers)

        # 3. Failover: check if provider is healthy
        if not await provider.health_check():
            # Find first alternative provider that is healthy
            for alt_name, alt_provider in self.providers.items():
                if alt_provider != provider and await alt_provider.health_check():
                    provider = alt_provider
                    break
            else:
                raise RuntimeError("No healthy providers available")


        # 4. Execute request + measure latency
        start_time = perf_counter()
        llm_result = await provider.send_request(
            prompt=req.prompt,
            model=model_name,
        )
        latency_ms = (perf_counter() - start_time) * 1000

        # 5. Async telemetry (FIXED)
        await self.telemetry.capture(
            request_id=req.metadata.get("request_id", str(uuid.uuid4())),
            provider=provider.name,
            model=model_name,
            usage=llm_result.usage,
            cost_estimated=llm_result.cost_estimated,
            latency_ms=latency_ms,
        )

        # 6. Unified FinOps response (FIXED)
        return FinObsResponse(
            id=str(uuid.uuid4()),
            content=llm_result.content,
            model_used=model_name,
            provider=provider.name,
            usage=llm_result.usage,
            cost_estimated=llm_result.cost_estimated,
            latency_ms=latency_ms,
        )

    def list_providers(self):
        return list(self.providers.keys())
