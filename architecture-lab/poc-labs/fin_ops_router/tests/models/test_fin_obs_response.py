import pytest
from pydantic import ValidationError

from finops_llm_router.models.fin_obs_response import FinObsResponse


def test_finobs_response_valid():
    res = FinObsResponse(
        id="123",
        content="processed text",
        model_used="gpt-4",
        provider="openai",
        usage={"input_tokens": 10, "output_tokens": 5},
        cost_estimated=0.001,
        latency_ms=12.5,
    )

    assert res.id == "123"
    assert res.content == "processed text"
    assert res.model_used == "gpt-4"
    assert res.provider == "openai"
    assert res.usage == {"input_tokens": 10, "output_tokens": 5}
    assert res.cost_estimated == 0.001
    assert res.latency_ms == 12.5


def test_finobs_response_missing_required_fields():
    with pytest.raises(ValidationError):
        FinObsResponse(
            id="123",
            content="ok",
            model_used="gpt-4",
            provider="openai",
            # missing usage, cost_estimated, latency_ms
        )


def test_finobs_response_wrong_type_usage():
    with pytest.raises(ValidationError):
        FinObsResponse(
            id="123",
            content="ok",
            model_used="gpt-4",
            provider="openai",
            usage="not-a-dict",
            cost_estimated=0.1,
            latency_ms=10.0,
        )


def test_finobs_response_wrong_type_cost_estimated():
    with pytest.raises(ValidationError):
        FinObsResponse(
            id="123",
            content="ok",
            model_used="gpt-4",
            provider="openai",
            usage={"input_tokens": 1, "output_tokens": 1},
            cost_estimated="not-a-float",
            latency_ms=10.0,
        )


def test_finobs_response_wrong_type_latency_ms():
    with pytest.raises(ValidationError):
        FinObsResponse(
            id="123",
            content="ok",
            model_used="gpt-4",
            provider="openai",
            usage={"input_tokens": 1, "output_tokens": 1},
            cost_estimated=0.1,
            latency_ms="not-a-float",
        )



