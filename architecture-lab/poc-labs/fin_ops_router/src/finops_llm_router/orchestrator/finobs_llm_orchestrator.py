import uuid
from time import perf_counter
from typing import Dict

from finops_llm_router.guardrails.guardrails import Guardrails
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.models.fin_obs_response import FinObsResponse
from finops_llm_router.orchestrator.cost_first_strategy import CostFirstStrategy
from finops_llm_router.orchestrator.performance_first_strategy import PerformanceFirstStrategy
from finops_llm_router.providers.base_provider import BaseProvider
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
            # Emit guardrail violation telemetry
            await self.capture_guardrail_violation(req=req)
            raise ValueError("Guardrail check failed")

        # 2. Strategy selection
        strategy = self.strategies.get(req.priority.lower())
        if not strategy:
            raise ValueError(f"Unknown routing strategy: {req.priority}")

        # 3. Select providers order from strategy
        ordered_providers = strategy.rank_providers(req, self.providers)
        if not ordered_providers:
            raise RuntimeError("No providers available for routing.")

        first_provider = ordered_providers[0]
        last_exception = None

        for provider in ordered_providers:
            try:
                model_name = strategy.select_model(req, provider)
                start_time = perf_counter()
                llm_result = await provider.send_request(prompt=req.prompt, model=model_name)
                latency_ms = (perf_counter() - start_time) * 1000

                # Determine if fallback was used
                fallback_used = first_provider != provider

                # 4. Telemetry for successful request
                await self.telemetry.capture(
                    request_id=req.id,
                    strategy=strategy.name,
                    provider=provider.name,
                    model=model_name,
                    usage=llm_result.usage,
                    cost_estimated=llm_result.cost_estimated,
                    latency_ms=latency_ms,
                    fallback_used=fallback_used,
                    provider_failed=False,
                    guardrail_failed=False,
                )

                # 5. Return unified response
                return FinObsResponse(
                    id=str(uuid.uuid4()),
                    content=llm_result.content,
                    model_used=model_name,
                    provider=provider.name,
                    usage=llm_result.usage,
                    cost_estimated=llm_result.cost_estimated,
                    latency_ms=latency_ms,
                )

            except Exception as e:
                last_exception = e
                # 6. Telemetry for failed provider
                await self.telemetry.capture(
                    request_id=req.id,
                    strategy=strategy.name,
                    provider=provider.name,
                    model=None,
                    usage=None,
                    cost_estimated=None,
                    latency_ms=None,
                    fallback_used=False,
                    provider_failed=True,
                    guardrail_failed=False,
                )
                print(f"[Orchestrator] Provider {provider.name} failed: {e}")
                continue

        # 7. If all providers fail
        raise RuntimeError(f"All providers failed. Last error: {last_exception}")

    def list_providers(self):
        return list(self.providers.keys())

    async def capture_guardrail_violation(self, req: FinObsRequest):
        """
        Emit telemetry for a guardrail violation.
        """
        await self.telemetry.capture(
            request_id=req.id,
            strategy="N/A",
            provider=None,
            model=None,
            usage=None,
            cost_estimated=None,
            latency_ms=None,
            guardrail_failed=True,
            guardrail_reason=self.guardrails.last_violation,
            fallback_used=False,
            provider_failed=False,
        )
