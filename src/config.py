from pydantic_settings import SettingsConfigDict, BaseSettings


class Setting(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    model_config = SettingsConfigDict(env_file="../.env-postgresql")


setting = Setting()
