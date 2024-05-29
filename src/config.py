from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    postgres_user: str = "test"
    postgres_password: str = "test"
    postgres_db: str = "testdb"
    postgres_host: str = "localhost"
    postgres_port: int = 5438


setting = Setting()

