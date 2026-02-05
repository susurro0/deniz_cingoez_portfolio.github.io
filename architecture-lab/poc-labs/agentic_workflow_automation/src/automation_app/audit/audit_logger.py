import json
import logging
from datetime import datetime
from typing import Any, Dict

from automation_app.models.plan import Plan
from automation_app.utils.pii_scrubber import PIIScrubber

logger = logging.getLogger("automation_audit")
logger.setLevel(logging.INFO)

class AuditLogger:

    @staticmethod
    def log(
        workflow_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ):
        record = {
            "workflow_id": workflow_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        logger.info(json.dumps(record))

    @staticmethod
    def log_plan(session_id: str, plan: Plan):
        """Helper to log plan in a PII-safe way"""
        plan_data = []
        for action in plan.actions:
            plan_data.append({
                "adapter": action.adapter,
                "method": action.method,
                "params": PIIScrubber().scrub_data(action.params),  # scrub PII
            })

        AuditLogger.log(
            session_id,
            "PLAN_GENERATED",
            {"actions": plan_data}
        )
