from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str = ""
    backend_cors_origins: str = "http://localhost:3000"

    # Email / SMTP (all optional — system works without them)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""   # defaults to smtp_username if blank

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",")]


settings = Settings()
