from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MyAIDoctor API"
    environment: str = "dev"
    log_level: str = "INFO"

    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@postgres:5432/myaidoctor")
    jwt_secret_key: str = Field(default="change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Comma-separated list of allowed CORS origins.
    # Examples:
    # - "http://localhost:3000"
    # - "http://your-host" (nginx on :80) and "http://your-host:3000" (direct Next dev)
    # - "*" (not recommended for production when allow_credentials=True)
    cors_allow_origins: str = (
        "http://localhost,http://localhost:3000,"
        "http://127.0.0.1,http://127.0.0.1:3000,"
        "http://20.197.0.41,http://20.197.0.41:3000,"
        "https://seliseproject.sharifsdevlab.me"
    )


settings = Settings()
