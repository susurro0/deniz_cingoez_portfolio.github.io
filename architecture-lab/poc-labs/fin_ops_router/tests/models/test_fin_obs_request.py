import pytest
from pydantic import ValidationError

from finops_llm_router.models.fin_obs_request import FinObsRequest


def test_finobs_request_valid_minimal():
    req = FinObsRequest(
        prompt="hello",
        task_type="summarization"
    )

    assert req.prompt == "hello"
    assert req.task_type == "summarization"
    assert req.priority == "cost"          # default
    assert req.metadata == {}              # default


def test_finobs_request_valid_full():
    req = FinObsRequest(
        prompt="hello",
        task_type="code",
        priority="performance",
        metadata={"source": "unit-test"}
    )

    assert req.prompt == "hello"
    assert req.task_type == "code"
    assert req.priority == "performance"
    assert req.metadata == {"source": "unit-test"}


def test_finobs_request_missing_prompt():
    with pytest.raises(ValidationError):
        FinObsRequest(task_type="general")


def test_finobs_request_missing_task_type():
    with pytest.raises(ValidationError):
        FinObsRequest(prompt="hello")


def test_finobs_request_wrong_type_prompt():
    with pytest.raises(ValidationError):
        FinObsRequest(prompt=123, task_type="general")


def test_finobs_request_wrong_type_metadata():
    with pytest.raises(ValidationError):
        FinObsRequest(prompt="hello", task_type="general", metadata="not-a-dict")


def test_finobs_request_allows_extra_fields():
    """
    Pydantic v2 default: extra='ignore'.
    Extra fields are accepted and stored.
    """
    req = FinObsRequest(
        prompt="hello",
        task_type="general",
        extra_field="ignored"
    )

    assert req.prompt == "hello"
    assert req.task_type == "general"
