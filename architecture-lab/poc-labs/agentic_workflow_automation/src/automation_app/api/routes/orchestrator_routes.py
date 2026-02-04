from fastapi import APIRouter
from pydantic import BaseModel

from automation_app.models.orchestrator_request import OrchestratorRequest
from automation_app.models.orchestrator_response import OrchestratorResponse


class OrchestratorRoutes:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self):
        @self.router.post(
            "/process",
            response_model=OrchestratorResponse
        )
        def process_request(req: OrchestratorRequest):
            result = self.orchestrator.process_request(
                user_input=req.text,
                session_id=req.session_id
            )
            return {"message": result}

        @self.router.post("/propose", response_model=OrchestratorResponse)
        def propose(req: OrchestratorRequest):
            result = self.orchestrator.propose(req.text, req.session_id)
            return {
                "message": result["message"],
                "state": result["state"],
                "plan": result.get("plan")
            }

        @self.router.post("/confirm", response_model=OrchestratorResponse)
        def confirm(req: OrchestratorRequest):
            result = self.orchestrator.confirm(req.session_id)
            return {
                "message": result["message"],
                "state": result["state"]
            }

        @self.router.post("/reject", response_model=OrchestratorResponse)
        def reject(req: OrchestratorRequest):
            result = self.orchestrator.reject(req.session_id)
            return {
                "message": result["message"],
                "state": result["state"]
            }
