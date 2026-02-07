import runpy
from unittest.mock import patch


def test_main_entrypoint_runs_uvicorn():
    with patch("automation_app.main.uvicorn.run") as mock_run:
        # Execute the file as if it were run with `python -m automation_app.main`
        runpy.run_module("automation_app.main", run_name="__main__")

        mock_run.assert_called_once_with(
            "automation_app.api.app_factory:app",
            host="0.0.0.0",
            port=8001,
            reload=True
        )
