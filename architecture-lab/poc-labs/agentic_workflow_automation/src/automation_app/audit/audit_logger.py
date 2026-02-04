import json
import logging
from datetime import datetime
from typing import Any, Dict

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
