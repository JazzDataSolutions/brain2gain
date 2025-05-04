from pydantic import BaseSettings, PostgresDsn

class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    SECRET_KEY: str

    class Config:
        env_file = ".env.dev"   # en prod apunta a .env
        env_file_encoding = "utf-8"

settings = Settings()

