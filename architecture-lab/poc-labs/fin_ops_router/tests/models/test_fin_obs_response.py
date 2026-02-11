import pytest
from pydantic import ValidationError

from finops_llm_router.models.fin_obs_response import FinObsResponse


def test_finobs_response_valid():
    res = FinObsResponse(
        prompt="Explain FinOps",
        response="FinOps is cloud financial management.",
        model_type="gpt-4"
    )

    assert res.prompt == "Explain FinOps"
    assert res.response == "FinOps is cloud financial management."
    assert res.model_type == "gpt-4"


def test_finobs_response_missing_prompt():
    with pytest.raises(ValidationError):
        FinObsResponse(
            response="ok",
            model_type="gpt-4"
        )


def test_finobs_response_missing_response():
    with pytest.raises(ValidationError):
        FinObsResponse(
            prompt="hello",
            model_type="gpt-4"
        )


def test_finobs_response_missing_model_type():
    with pytest.raises(ValidationError):
        FinObsResponse(
            prompt="hello",
            response="ok"
        )


def test_finobs_response_wrong_type_prompt():
    with pytest.raises(ValidationError):
        FinObsResponse(
            prompt=123,
            response="ok",
            model_type="gpt-4"
        )


def test_finobs_response_wrong_type_response():
    with pytest.raises(ValidationError):
        FinObsResponse(
            prompt="hello",
            response=999,
            model_type="gpt-4"
        )


def test_finobs_response_wrong_type_model_type():
    with pytest.raises(ValidationError):
        FinObsResponse(
            prompt="hello",
            response="ok",
            model_type=123
        )


def test_finobs_response_allows_extra_fields():
    """
    FinObsResponse uses Pydantic's default behavior: extra='ignore'.
    Extra fields are accepted and stored.
    """
    res = FinObsResponse(
        prompt="hi",
        response="ok",
        model_type="gpt-4",
        extra_field="ignored"
    )

    assert res.prompt == "hi"
    assert res.response == "ok"
    assert res.model_type == "gpt-4"
