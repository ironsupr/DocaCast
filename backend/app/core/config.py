from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Adobe Hackathon Finale API"
    environment: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
