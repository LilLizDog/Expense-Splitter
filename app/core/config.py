import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError


# Detect testing mode BEFORE loading settings
TESTING = os.getenv("TESTING") == "1"


class Settings(BaseSettings):
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


try:
    settings = Settings()

    # Only enforce required env vars when NOT testing
    if not TESTING:
        missing = []
        if not settings.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not settings.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")

        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Make sure they are set in your .env file or container env before starting the backend."
            )

except ValidationError as e:
    # Pydantic reports missing fields here
    if TESTING:
        # allow missing vars during tests
        settings = Settings(SUPABASE_URL="", SUPABASE_KEY="")
    else:
        # format missing keys nicely
        missing_fields = []
        for err in e.errors():
            if "missing" in err.get("type", ""):
                loc = err.get("loc", [])
                if loc:
                    missing_fields.append(loc[0])

        if missing_fields:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing_fields)}."
            ) from e

        raise RuntimeError(
            "Environment validation failed:\n" + str(e)
        ) from e
