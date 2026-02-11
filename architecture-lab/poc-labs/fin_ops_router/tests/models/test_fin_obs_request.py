import pytest
from pydantic import ValidationError

from finops_llm_router.models.fin_obs_request import FinObsRequest


def test_finobs_request_valid():
    req = FinObsRequest(prompt="Explain FinOps", model_type="gpt-4")
    assert req.prompt == "Explain FinOps"
    assert req.model_type == "gpt-4"


def test_finobs_request_missing_prompt():
    with pytest.raises(ValidationError):
        FinObsRequest(model_type="gpt-4")


def test_finobs_request_missing_model_type():
    with pytest.raises(ValidationError):
        FinObsRequest(prompt="hello")


def test_finobs_request_wrong_type_prompt():
    with pytest.raises(ValidationError):
        FinObsRequest(prompt=123, model_type="gpt-4")


def test_finobs_request_wrong_type_model_type():
    with pytest.raises(ValidationError):
        FinObsRequest(prompt="hello", model_type=999)


def test_finobs_request_allows_extra_fields():
    req = FinObsRequest(prompt="hi", model_type="gpt-4", extra_field="ignored")
    assert req.prompt == "hi"
    assert req.model_type == "gpt-4" # Extra field is ignored but still accessible as attribute assert req.extra_field == "ignored"