from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "local"
    APP_NAME: str = "transactional-control"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/tc"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    JWT_SECRET: str = "dev_secret_change_me"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:3000"

    DEADLINE_CHECK_MINUTES: int = 15


settings = Settings()
