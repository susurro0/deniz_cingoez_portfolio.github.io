import pytest
from automation_app.utils.pii_scrubber import PIIScrubber


# ---------------------------------------------------------------------------
# Basic PII scrubbing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, pii, expected",
    [
        ("Contact me at", "john.doe@example.com", "Contact me at ***"),
        ("My email is", "a.b+c-d@domain.co.uk", "My *** is ***"),
        ("Call me at", "555-123-4567", "Call me at ***"),
        ("SSN:", "123-45-6789", "*** : ***"),
        ("Card:", "4111 1111 1111 1111", "Card: ***"),
        ("IP:", "192.168.1.1", "IP: ***"),
    ],
    ids=[
        "email",
        "email_complex",
        "phone",
        "ssn",
        "credit_card",
        "ip_address",
    ],
)
def test_scrubber_single_pii(text, pii, expected):
    scrubber = PIIScrubber()

    assert scrubber.scrub(" ".join([text, pii])) == expected


# ---------------------------------------------------------------------------
# Multiple PII in one string
# ---------------------------------------------------------------------------

def test_scrubber_multiple_pii():
    text = "Email john@example.com and call 555-222-3333. SSN 123-45-6789"
    scrubber = PIIScrubber()
    result = scrubber.scrub(text)

    assert result == "*** *** and call ***. *** ***"


# ---------------------------------------------------------------------------
# Custom mask
# ---------------------------------------------------------------------------

def test_scrubber_custom_mask():
    scrubber = PIIScrubber(mask="[REDACTED]")
    text = "john@example.com"
    assert scrubber.scrub(text) == "[REDACTED]"


# ---------------------------------------------------------------------------
# No PII → unchanged
# ---------------------------------------------------------------------------

def test_scrubber_no_pii():
    scrubber = PIIScrubber()
    text = "Hello world, nothing sensitive here"
    assert scrubber.scrub(text) == text


# ---------------------------------------------------------------------------
# Non-string input
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_input", [123, None, {}, [], 3.14])
def test_scrubber_raises_on_non_string(bad_input):
    scrubber = PIIScrubber()
    with pytest.raises(TypeError):
        scrubber.scrub(bad_input)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_scrubber_multiple_occurrences_of_same_type():
    scrubber = PIIScrubber()
    text = "Emails: a@b.com, c@d.com"
    assert scrubber.scrub(text) == "Emails: ***, ***"


def test_scrubber_credit_card_with_dashes_and_spaces():
    scrubber = PIIScrubber()
    text = "Card: 4111-1111-1111-1111 or 4111 1111 1111 1111"
    assert scrubber.scrub(text) == "Card: *** or ***"


def test_scrubber_phone_formats():
    scrubber = PIIScrubber()
    text = "Call (555) 123 4567 or +1-555-123-4567"
    assert scrubber.scrub(text) == "Call ( *** or + ***"


def test_scrubber_ip_edge_case():
    scrubber = PIIScrubber()
    text = "Ping 999.999.999.999 should not match"
    # This is not a valid IP but matches the regex → scrubbed
    assert scrubber.scrub(text) == "Ping *** should not match"


def test_scrubber_mixed_pii_complex():
    scrubber = PIIScrubber()
    text = "Email a@b.com, phone 555-111-2222, IP 10.0.0.1, SSN 123-45-6789"
    result = scrubber.scrub(text)
    assert result == "*** ***, phone ***, IP ***, *** ***"

def test_scrub_data_string():
    scrubber = PIIScrubber()
    assert scrubber.scrub_data("john@example.com") == "***"


def test_scrub_data_dict():
    scrubber = PIIScrubber()
    data = {
        "email": "john@example.com",
        "safe": "hello",
    }
    result = scrubber.scrub_data(data)

    assert result == {
        "email": "***",
        "safe": "hello",
    }


def test_scrub_data_list():
    scrubber = PIIScrubber()
    data = ["john@example.com", "hello"]
    result = scrubber.scrub_data(data)

    assert result == ["***", "hello"]


def test_scrub_data_nested_structures():
    scrubber = PIIScrubber()
    data = {
        "users": [
            {"email": "a@b.com"},
            {"email": "c@d.com"},
        ],
        "meta": {
            "ip": "192.168.1.1",
            "notes": ["call 555-123-4567", "ok"],
        },
    }

    result = scrubber.scrub_data(data)

    assert result == {
        "users": [
            {"email": "***"},
            {"email": "***"},
        ],
        "meta": {
            "ip": "***",
            "notes": ["call ***", "ok"],
        },
    }


def test_scrub_data_non_string_values_are_converted():
    scrubber = PIIScrubber()
    data = {
        "int": 123,
        "float": 3.14,
        "bool": True,
        "none": None,
    }

    result = scrubber.scrub_data(data)

    # None, True, 123, 3.14 → converted to strings → scrubbed
    assert result == {
        "int": "123",
        "float": "3.14",
        "bool": "True",
        "none": "None",
    }


def test_scrub_data_mixed_list():
    scrubber = PIIScrubber()
    data = [
        "john@example.com",
        123,
        {"phone": "555-111-2222"},
        [None, "hello"],
    ]

    result = scrubber.scrub_data(data)

    assert result == [
        "***",
        "123",
        {"phone": "***"},
        ["None", "hello"],
    ]


def test_scrub_data_deeply_nested():
    scrubber = PIIScrubber()
    data = {
        "level1": [
            {
                "level2": {
                    "level3": [
                        "a@b.com",
                        {"ssn": "123-45-6789"},
                    ]
                }
            }
        ]
    }

    result = scrubber.scrub_data(data)

    assert result == {
        "level1": [
            {
                "level2": {
                    "level3": [
                        "***",
                        {"ssn": "***"},
                    ]
                }
            }
        ]
    }


def test_scrub_data_no_pii():
    scrubber = PIIScrubber()
    data = {"msg": "hello world"}
    assert scrubber.scrub_data(data) == {"msg": "hello world"}
