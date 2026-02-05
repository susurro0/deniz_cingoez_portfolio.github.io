from __future__ import annotations
import traceback
from automation_app.audit.audit_logger import AuditLogger
from automation_app.models.plan import Plan
from automation_app.utils.pii_scrubber import PIIScrubber


class ExecutionEngine:
    def __init__(self, adapters: dict, state_store=None, auditor=AuditLogger, scrubber=None):
        """
        adapters: dict of adapter_name -> adapter_instance
        state_store: optional persistent store for saga state
        auditor: AuditLogger class or custom logger (for easier testing)
        scrubber: PIIScrubber class
        """
        self.adapters = adapters
        self.state_store = state_store
        self.auditor = auditor
        self.scrubber = scrubber or PIIScrubber()

    def run(self, plan: Plan, session_id: str = None) -> bool:
        """
        Execute a plan action by action, logging and persisting each step.
        Returns True if all actions succeed, False if any fail.
        """
        action_results = []

        for idx, action in enumerate(plan.actions):
            scrubbed_params = self.scrubber.scrub_data(action.params)
            self._audit(session_id, "ACTION_STARTED", {
                "adapter": action.adapter,
                "method": action.method,
                "params": scrubbed_params,
                "step": idx
            })
            self._save_state(session_id, plan, idx, "STARTED")

            adapter = self.adapters.get(action.adapter)
            if not adapter:
                self._audit(session_id, "ACTION_FAILED", {
                    "adapter": action.adapter,
                    "method": action.method,
                    "step": idx,
                    "error": f"No adapter found for {action.adapter}"
                })
                self.rollback(plan, up_to_step=idx, session_id=session_id)
                return False

            if not self._is_action_supported(adapter, action.method):
                self._audit(session_id, "EXECUTION_FAILED", {
                    "adapter": action.adapter,
                    "method": action.method,
                    "step": idx,
                    "error": f"Action '{action.method}' not supported by adapter '{action.adapter}'"
                })
                self.rollback(plan, up_to_step=idx, session_id=session_id)
                return False

            try:
                adapter.execute(action.method, action.params)
                self._audit(session_id, "ACTION_SUCCEEDED", {
                    "adapter": action.adapter,
                    "method": action.method,
                    "step": idx
                })
                self._save_state(session_id, plan, idx, "SUCCEEDED")
                action_results.append({"step": idx, "status": "SUCCEEDED"})

            except Exception as e:
                self._audit(session_id, "ACTION_FAILED", {
                    "adapter": action.adapter,
                    "method": action.method,
                    "step": idx,
                    "error": str(e),
                    "trace": traceback.format_exc()
                })
                self._save_state(session_id, plan, idx, "FAILED")
                self.rollback(plan, up_to_step=idx, session_id=session_id)
                return False

        return True

    def rollback(self, plan: Plan, up_to_step: int = None, session_id: str = None):
        """
        Rollback executed actions in reverse order up to up_to_step index (exclusive).
        Uses a cleaner slice-and-reverse approach for better readability.
        """
        # Determine the range of actions that need undoing
        # If up_to_step is 3, we rollback indices 2, 1, 0.
        limit = up_to_step if up_to_step is not None else len(plan.actions)
        actions_to_undo = list(enumerate(plan.actions))[:limit]

        for idx, action in reversed(actions_to_undo):
            adapter = self.adapters.get(action.adapter)

            # Use getattr to safely check for the compensate method
            compensate_func = getattr(adapter, "compensate", None)

            if not compensate_func:
                continue

            # Scrub params even for rollback—PII is still PII during a failure!
            scrubbed_params = self.scrubber.scrub_data(action.params)

            try:
                compensate_func(action.method, action.params)
                self._audit(session_id, "ACTION_COMPENSATED", {
                    "adapter": action.adapter,
                    "method": action.method,
                    "step": idx,
                    "params": scrubbed_params
                })
            except Exception as e:
                self._audit(session_id, "ACTION_COMPENSATION_FAILED", {
                    "adapter": action.adapter,
                    "method": action.method,
                    "step": idx,
                    "error": str(e),
                    "trace": traceback.format_exc(),
                    "params": scrubbed_params
                })
    # --------------------
    # Helper methods
    # --------------------
    def _is_action_supported(self, adapter, method: str) -> bool:
        """Check if the adapter supports the given action method"""
        return method in getattr(adapter, "supported_actions", lambda: [])()

    def _save_state(self, session_id, plan, step_idx: int, status: str):
        if not (self.state_store and session_id):
            return
        try:
            self.state_store.save_context(session_id, {
                "last_plan": plan.dict(),
                "last_action_index": step_idx,
                "last_action_status": status
            })
        except Exception as e:
            # Don't let the state store crash the engine, but DO audit the failure
            self._audit(session_id, "STATE_STORE_FAILURE", {"error": str(e)})

    def _audit(self, session_id, event_type: str, payload: dict):
        """Wrapper for auditing actions"""
        self.auditor.log(session_id, event_type, payload)
