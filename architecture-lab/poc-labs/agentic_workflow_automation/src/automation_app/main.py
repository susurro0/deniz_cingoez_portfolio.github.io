# automation_app/main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "automation_app.api.app_factory:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
