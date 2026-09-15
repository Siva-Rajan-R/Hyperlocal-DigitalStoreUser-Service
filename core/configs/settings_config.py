from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8011
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "DigitalStoreUserServiceDb"
    ENVIRONMENT: str = "development"
    SHOP_SERVICE_URL: str = "http://127.0.0.1:8001"

    class Config:
        env_file = ".env"
        extra = "ignore"

SETTINGS = Settings()
