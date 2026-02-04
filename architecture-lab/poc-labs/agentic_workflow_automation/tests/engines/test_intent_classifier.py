# tests/engines/test_intent_classifier.py
import pytest

from automation_app.engines.intent_classifier import IntentClassifier
from automation_app.models.intent import Intent


def test_classifies_pto_basic():
    clf = IntentClassifier()
    intent = clf.classify("I need PTO next Friday")
    assert intent.type == "PTO"
    assert intent.entity == "date"


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
def test_classifies_pto_variants(text):
    clf = IntentClassifier()
    intent = clf.classify(text)
    assert intent.type == "PTO"
    assert intent.entity == "date"


def test_classify_unknown_intent():
    clf = IntentClassifier()
    with pytest.raises(ValueError) as exc:
        clf.classify("Schedule a meeting with John")

    assert "Unknown intent" in str(exc.value)


def test_classifier_returns_intent_model():
    clf = IntentClassifier()
    intent = clf.classify("PTO request")
    assert isinstance(intent, Intent)
