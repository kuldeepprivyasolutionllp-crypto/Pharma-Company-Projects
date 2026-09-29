from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/amneal"
    jwt_secret: str = "local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:8369"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
