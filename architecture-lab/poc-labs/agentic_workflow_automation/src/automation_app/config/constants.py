HITL_TIMEOUT_SECONDS = 3600
MAX_RETRIES = 3
BASE_BACKOFF = 0.5

class RecoveryDecision:
    RETRY = "retry"
    REPLAN = "replan"
    FAIL = "fail"
