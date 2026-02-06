# tests/engines/test_intent_classifier.py
import pytest

from automation_app.engines.intent_classifier import IntentClassifier
from automation_app.models.intent import Intent

@pytest.mark.asyncio
async def test_classifies_pto_basic():
    clf = IntentClassifier()
    intent = await clf.classify("I need PTO next Friday")
    assert intent.type == "PTO"
    assert intent.entity == "date"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "Requesting PTO",
        "I want some time off",
        "TIME OFF tomorrow",
        "pto please",
        "Can I take Time Off next week?",
    ],
)
async def test_classifies_pto_variants(text):
    clf = IntentClassifier()
    intent = await clf.classify(text)
    assert intent.type == "PTO"
    assert intent.entity == "date"


@pytest.mark.asyncio
async def test_classify_unknown_intent():
    clf = IntentClassifier()
    with pytest.raises(ValueError) as exc:
        await clf.classify("Schedule a meeting with John")

    assert "Unknown intent" in str(exc.value)


@pytest.mark.asyncio
async def test_classifier_returns_intent_model():
    clf = IntentClassifier()
    intent = await clf.classify("PTO request")
    assert isinstance(intent, Intent)
