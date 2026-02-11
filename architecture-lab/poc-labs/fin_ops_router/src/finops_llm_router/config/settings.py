import os

class Settings:
    """
    Application configuration settings.
    """

    def __init__(self):
        self.DB_URL = os.getenv("DB_URL", "sqlite:///telemetry.db")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
