from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8011
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "DigitalStoreUserServiceDb"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"

SETTINGS = Settings()
