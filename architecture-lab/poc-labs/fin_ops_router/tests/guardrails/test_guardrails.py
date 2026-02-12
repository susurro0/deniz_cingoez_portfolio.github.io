import pytest

from finops_llm_router.guardrails.guardrails import Guardrails


@pytest.fixture
def guardrails():
    return Guardrails()


def test_validate_allows_clean_prompt(guardrails):
    prompt = "Tell me about cloud cost optimization strategies."
    assert guardrails.validate(prompt) is True


def test_validate_blocks_prompt_with_ssn(guardrails):
    prompt = "The user's SSN is 123-45-6789."
    assert guardrails.validate(prompt) is False


def test_validate_blocks_prompt_with_credit_card(guardrails):
    prompt = "My credit card number is 4111 1111 1111 1111."
    assert guardrails.validate(prompt) is False


def test_validate_blocks_prompt_with_multiple_forbidden_keywords(guardrails):
    prompt = "SSN and credit card details are included."
    assert guardrails.validate(prompt) is False


def test_validate_is_case_sensitive(guardrails):
    """
    Current implementation is case-sensitive.
    'ssn' should NOT be detected unless uppercase.
    """
    prompt = "the user's ssn is not uppercase"
    assert guardrails.validate(prompt) is True


def test_validate_partial_word_does_not_trigger(guardrails):
    """
    Ensures substring matches don't accidentally trigger.
    Example: 'assignment' contains 'ssn' but should not be blocked.
    """
    prompt = "This is an assignment for class."
    assert guardrails.validate(prompt) is True
