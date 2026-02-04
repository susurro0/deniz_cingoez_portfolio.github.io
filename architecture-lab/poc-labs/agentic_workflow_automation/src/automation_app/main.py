import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "automation_app.api.app_factory:AppFactory().get_app()",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
