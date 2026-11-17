"""AgriConnect application configuration."""

import os
from pathlib import Path
from typing import List

# Resolve base backend directory (AgriHUB/backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = BACKEND_DIR / "agriconnect.db"

# Load local .env if present
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


class Settings:
    PROJECT_NAME: str = "AgriConnect"
    API_V1_STR: str = "/api/v1"
    
    # Always resolve SQLite database to backend/agriconnect.db regardless of launch CWD
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    )
    
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # JWT Authentication Settings
    # Mandatory from environment; no insecure default fallback string!
    # Validated during startup lifespan in app/main.py
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


settings = Settings()
