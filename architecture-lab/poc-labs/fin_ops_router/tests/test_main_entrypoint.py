import runpy
from unittest.mock import patch


def test_main_entrypoint_runs_uvicorn():
    with patch("main.uvicorn.run") as mock_run:
        # Execute the file as if it were run with `python -m automation_app.main`
        runpy.run_module("main", run_name="__main__")

        mock_run.assert_called_once_with(
            "finops_llm_router.api.app_factory:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
