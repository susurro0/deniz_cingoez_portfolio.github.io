# automation_app/engines/recovery_engine.py

from typing import Any
import asyncio
import traceback

from automation_app.audit.audit_logger import AuditLogger
from automation_app.config.constants import RecoveryDecision
from automation_app.engines.exceptions import ActionFailure


class RecoveryEngine:
    def __init__(
        self,
        max_retries: int = 3,
        base_backoff: float = 0.5,
        auditor=AuditLogger,
    ):
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.auditor = auditor

    async def attempt_with_recovery(
        self,
        *,
        execute_fn,
        action,
        session_id: str,
        step_idx: int,
    ):
        """
        Executes an action with retry + backoff.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                return await execute_fn()

            except Exception as exc:
                last_exc = exc

                decision = self._classify_error(exc)

                self.auditor.log(
                    session_id,
                    "ATTEMPT FAILED",
                    {
                        "step": step_idx,
                        "attempt": attempt,
                        "decision": str(decision),
                        "error": str(exc),
                        "trace": traceback.format_exc(),
                    },
                )

                if decision == RecoveryDecision.RETRY and attempt < self.max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue

                raise  ActionFailure(decision, exc)

    def _classify_error(self, exc: Exception) -> str:
        """
        Naive classification for now.
        Later: adapter-specific errors, HTTP codes, etc.
        """
        msg = str(exc).lower()

        if any(keyword in msg for keyword in [
            "timeout",
            "temporarily unavailable",
            "rate limit",
            "connection reset",
            "503",
        ]):
            return RecoveryDecision.RETRY

        if any(keyword in msg for keyword in [
            "permission",
            "not authorized",
            "forbidden",
            "403",
        ]):
            return RecoveryDecision.PERMISSION

        if any(keyword in msg for keyword in [
            "not supported",
            "unsupported action",
            "unknown method",
        ]):
            return RecoveryDecision.NOT_SUPPORTED

        return RecoveryDecision.UNKNOWN

    def _backoff(self, attempt: int) -> float:
        return self.base_backoff * (2 ** (attempt - 1))
