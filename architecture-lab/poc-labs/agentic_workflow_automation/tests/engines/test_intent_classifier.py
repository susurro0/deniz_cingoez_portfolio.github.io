import pytest
from automation_app.engines.intent_classifier import IntentClassifier
from automation_app.models.intent import Intent


# ----------------------------------------------------------------------
# PTO classification
# ----------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "I need PTO next Friday",
        "Requesting PTO",
        "I want some time off",
        "TIME OFF tomorrow",
        "pto please",
        "Can I take Time Off next week?",
    ],
)
async def test_classifies_pto(text):
    clf = IntentClassifier()
    intent = await clf.classify(text)

    assert intent.name == "REQUEST_TIME_OFF"
    assert intent.adapter == "Workday"
    assert intent.method == "create_time_off"
    assert isinstance(intent.entities, dict)
    assert intent.entities == {}   # stubbed extractor


# ----------------------------------------------------------------------
# Email classification
# ----------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "Send an email to John",
        "Email the team",
        "Can you mail this?",
        "Please send mail asap",
    ],
)
async def test_classifies_email(text):
    clf = IntentClassifier()
    intent = await clf.classify(text)

    assert intent.name == "SEND_EMAIL"
    assert intent.adapter == "MSGraph"
    assert intent.method == "send_email"
    assert isinstance(intent.entities, dict)
    assert intent.entities == {}   # stubbed extractor


# ----------------------------------------------------------------------
# Calendar classification
# ----------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "Schedule a meeting",
        "Set up a calendar event",
        "I need a meeting tomorrow",
        "Can you schedule something?",
    ],
)
async def test_classifies_calendar(text):
    clf = IntentClassifier()
    intent = await clf.classify(text)

    assert intent.name == "CREATE_CALENDAR_EVENT"
    assert intent.adapter == "MSGraph"
    assert intent.method == "create_calendar_event"
    assert isinstance(intent.entities, dict)
    assert intent.entities == {}   # stubbed extractor


# ----------------------------------------------------------------------
# Unknown intent
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classify_unknown_intent():
    clf = IntentClassifier()

    with pytest.raises(ValueError):
        await clf.classify("I like turtles")   # truly unknown


# ----------------------------------------------------------------------
# Intent model type
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classifier_returns_intent_model():
    clf = IntentClassifier()
    intent = await clf.classify("PTO request")

    assert isinstance(intent, Intent)
