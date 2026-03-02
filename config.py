import json
import os
from typing import Optional

from pydantic_settings import BaseSettings


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


class Settings(BaseSettings):
    """
    Runtime settings for external LLM API.

    Priority:
    1. config.json (user editable)
    2. Environment variables as fallback
    3. Hard-coded defaults as last resort
    """

    external_api_base_url: str = os.getenv(
        "EXTERNAL_API_BASE_URL", "https://api.openai.com/v1"
    )
    external_api_key: str = os.getenv("EXTERNAL_API_KEY", "")
    web_model: str = os.getenv("WEB_MODEL", "gpt-3.5-turbo")
    api_key: str = os.getenv("API_KEY", "")


def load_settings() -> Settings:
    """Load settings from config.json if it exists, otherwise from env/defaults."""
    base = Settings()

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # If the file is broken, fall back to env/defaults
            return base

        # Only override known fields
        for field in ("external_api_base_url", "external_api_key", "web_model", "api_key"):
            if field in data and data[field] is not None:
                setattr(base, field, data[field])

    return base


def save_settings(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    web_model: Optional[str] = None,
    local_api_key: Optional[str] = None,
) -> Settings:
    """
    Persist user settings to config.json and return the updated Settings instance.
    Parameters that are None will keep their current values.
    """
    settings = load_settings()

    if base_url is not None:
        settings.external_api_base_url = base_url
    if api_key is not None:
        settings.external_api_key = api_key
    if web_model is not None:
        settings.web_model = web_model
    if local_api_key is not None:
        settings.api_key = local_api_key

    data = {
        "external_api_base_url": settings.external_api_base_url,
        "external_api_key": settings.external_api_key,
        "web_model": settings.web_model,
        "api_key": settings.api_key,
    }

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        # If writing fails, we still return the in-memory settings
        pass

    return settings

