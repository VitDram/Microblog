from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int


setting = Setting()

