from fastapi import APIRouter
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
        async def process_request(req: OrchestratorRequest):
            # Added 'await' because orchestrator is now async
            result = await self.orchestrator.process_request(
                user_input=req.text,
                session_id=req.session_id,
                user_id=req.user_id if hasattr(req, 'user_id') else "anonymous",
                role=req.role,
                department=req.department
            )
            return {"message": result}

        @self.router.post("/propose", response_model=OrchestratorResponse)
        async def propose(req: OrchestratorRequest):
            result = await self.orchestrator.propose(
                user_input=req.text,
                session_id=req.session_id,
                user_id=req.user_id,
                role=req.role,
                department=req.department
            )
            # Standardizing the response mapping
            return {
                "message": result["message"],
                "state": result["state"],
                "plan": result.get("plan")
            }

        @self.router.post("/confirm", response_model=OrchestratorResponse)
        async def confirm(req: OrchestratorRequest):
            result = await self.orchestrator.confirm(req.session_id)
            return {
                "message": result["message"],
                "state": result.get("state")
            }

        @self.router.post("/reject", response_model=OrchestratorResponse)
        async def reject(req: OrchestratorRequest):
            result = await self.orchestrator.reject(req.session_id)
            return {
                "message": result["message"],
                "state": result.get("state")
            }