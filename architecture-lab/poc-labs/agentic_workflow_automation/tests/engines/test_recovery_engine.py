import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from automation_app.config.constants import RecoveryDecision
from automation_app.engines.recovery_engine import RecoveryEngine

@pytest.fixture
def engine():
    return RecoveryEngine()

@pytest.mark.asyncio
async def test_attempt_with_recovery_success_first_try():
    auditor = MagicMock()
    engine = RecoveryEngine(auditor=auditor)

    execute_fn = AsyncMock(return_value="OK")

    result = await engine.attempt_with_recovery(
        execute_fn=execute_fn,
        action=None,
        session_id="s1",
        step_idx=0,
    )

    assert result == "OK"
    execute_fn.assert_awaited_once()
    auditor.log.assert_not_called()


@pytest.mark.asyncio
async def test_attempt_with_recovery_retry_then_success():
    auditor = MagicMock()
    engine = RecoveryEngine(auditor=auditor, max_retries=3)

    # First call fails, second succeeds
    execute_fn = AsyncMock(side_effect=[Exception("timeout"), "OK"])

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        result = await engine.attempt_with_recovery(
            execute_fn=execute_fn,
            action=None,
            session_id="s1",
            step_idx=1,
        )

    assert result == "OK"
    assert execute_fn.await_count == 2
    auditor.log.assert_called_once()
    mock_sleep.assert_awaited_once()  # backoff happened


@pytest.mark.asyncio
async def test_attempt_with_recovery_fails_after_max_retries():
    auditor = MagicMock()
    engine = RecoveryEngine(auditor=auditor, max_retries=2)

    execute_fn = AsyncMock(side_effect=Exception("timeout"))

    with patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(Exception):
            await engine.attempt_with_recovery(
                execute_fn=execute_fn,
                action=None,
                session_id="s1",
                step_idx=2,
            )

    assert execute_fn.await_count == 2  # max retries
    assert auditor.log.call_count == 2  # logged both failures


@pytest.mark.asyncio
async def test_attempt_with_recovery_fail_immediately_on_non_retry_error():
    auditor = MagicMock()
    engine = RecoveryEngine(auditor=auditor)

    execute_fn = AsyncMock(side_effect=Exception("fatal error"))

    with pytest.raises(Exception):
        await engine.attempt_with_recovery(
            execute_fn=execute_fn,
            action=None,
            session_id="s1",
            step_idx=3,
        )

    execute_fn.assert_awaited_once()
    auditor.log.assert_called_once()


def test_classify_error_retry():
    engine = RecoveryEngine()
    assert engine._classify_error(Exception("Timeout occurred")) == RecoveryDecision.RETRY
    assert engine._classify_error(Exception("temporarily unavailable")) == RecoveryDecision.RETRY

@pytest.mark.parametrize(
    "msg",
    [
        "timeout occurred",
        "temporarily unavailable",
        "rate limit exceeded",
        "connection reset by peer",
        "503 service unavailable",
    ],
)
def test_classify_retry(engine, msg):
    exc = Exception(msg)
    decision = engine._classify_error(exc)
    assert decision == RecoveryDecision.RETRY


@pytest.mark.parametrize(
    "msg",
    [
        "random failure",
        "unexpected error",
        "boom",
        "internal server meltdown",
    ],
)
def test_classify_unknown(engine, msg):
    exc = Exception(msg)
    decision = engine._classify_error(exc)
    assert decision == RecoveryDecision.UNKNOWN

@pytest.mark.parametrize(
    "msg",
    [
        "This action is not supported",
        "Unsupported action: create_user",
        "Unknown method foo_bar",
    ],
)
def test_classify_not_supported(engine, msg):
    exc = Exception(msg)
    decision = engine._classify_error(exc)
    assert decision == RecoveryDecision.NOT_SUPPORTED


@pytest.mark.parametrize(
    "msg",
    [
        "Permission denied",
        "User not authorized",
        "Forbidden operation",
        "Error 403: forbidden",
    ],
)
def test_classify_permission(engine, msg):
    exc = Exception(msg)
    decision = engine._classify_error(exc)
    assert decision == RecoveryDecision.PERMISSION


def test_backoff_calculation():
    engine = RecoveryEngine(base_backoff=0.5)

    assert engine._backoff(1) == 0.5
    assert engine._backoff(2) == 1.0
    assert engine._backoff(3) == 2.0
