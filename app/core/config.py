from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        )

try:
    settings = Settings()
except ValidationError as e:
    # Pydantic already knows what's missing, we just format it pretty
    missing_fields = []

    for err in e.errors():
        # err["loc"] is a tuple like ("SUPABASE_URL",)
        if err.get("type") == "missing" or "missing" in err.get("type", ""):
            loc = err.get("loc", [])
            if loc:
                missing_fields.append(str(loc[0]))

    if not missing_fields:
        # fall back to generic error if we can't parse nicely
        raise RuntimeError(
            "Environment validation failed. Details:\n"
            f"{e}"
        ) from e

    missing_str = ", ".join(missing_fields)
    raise RuntimeError(
        f"Missing required environment variables: {missing_str}. "
        "Make sure they are set in your .env file or container env before starting the backend."
    ) from e
