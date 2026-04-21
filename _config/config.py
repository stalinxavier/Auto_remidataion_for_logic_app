"""
_config/config.py
-----------------
Loads all environment variables from .env and exposes them as a single Settings object.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Azure Service Principal
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")

    # Azure Resource Targeting
    AZURE_SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_RESOURCE_GROUP: str = os.getenv("AZURE_RESOURCE_GROUP", "")
    LOGIC_APP_NAME: str = os.getenv("LOGIC_APP_NAME", "")

    # Log Analytics
    LOG_ANALYTICS_WORKSPACE_ID: str = os.getenv("LOG_ANALYTICS_WORKSPACE_ID", "")

    # AI Core / LLM
    AICORE_BASE_URL: str = os.getenv("AICORE_BASE_URL", "")
    LLM_DEPLOYMENT_ID: str = os.getenv("LLM_DEPLOYMENT_ID", "")
    AICORE_CLIENT_ID: str = os.getenv("AICORE_CLIENT_ID", "")
    AICORE_CLIENT_SECRET: str = os.getenv("AICORE_CLIENT_SECRET", "")
    AICORE_AUTH_URL: str = os.getenv("AICORE_AUTH_URL", "")
    AICORE_RESOURCE_GROUP: str = os.getenv("AICORE_RESOURCE_GROUP", "default")

    # ARM API version for Logic Apps
    ARM_API_VERSION: str = "2019-05-01"

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing required env vars."""
        required = [
            "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
            "AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP",
        ]
        return [k for k in required if not getattr(cls, k)]


settings = Settings()
