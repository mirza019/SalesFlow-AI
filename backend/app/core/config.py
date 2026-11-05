from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./salesflow.db"
    secret_key: str = "change-me"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

