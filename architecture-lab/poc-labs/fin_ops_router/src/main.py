import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "finops_llm_router.api.app_factory:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )

