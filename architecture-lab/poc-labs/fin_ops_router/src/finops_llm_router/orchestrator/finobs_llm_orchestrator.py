from __future__ import annotations

from finops_llm_router.guardrails.guardrails import Guardrails
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.models.fin_obs_response import FinObsResponse
from finops_llm_router.providers.openai_provider import OpenAIProvider
from finops_llm_router.telemetry.collector import TelemetryCollector


class FinObsLLMOrchestrator:
    def __init__(
        self, guardrails: Guardrails, telemetry: TelemetryCollector
    ):
        self.providers = {
            "openai": OpenAIProvider(),
            # Other providers can be added here
        }
        self.guardrails = guardrails
        self.telemetry = telemetry

    async def handle(self, req: FinObsRequest) -> FinObsResponse:
        if not self.guardrails.validate(req.prompt):
            raise ValueError("Guardrail check failed")

        if req.model_type.lower() == "cost":
            provider = self.providers["openai"]
            model_name = "GPT-4o-mini"
        else:
            provider = self.providers["openai"]
            model_name = "GPT-4"

        response = await provider.send_request(req.prompt, model_name)

        await self.telemetry.capture(
            prompt=req.prompt,
            response=response,
            model_used=model_name,
        )

        return FinObsResponse(
            prompt=req.prompt,
            response=response,
            model_type=model_name,
        )

    def list_providers(self):
        return list(self.providers.keys())
