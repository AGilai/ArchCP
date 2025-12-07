from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SASE Provisioning Service"
    TENANT_ID: str = "tenant-cp"

    # Infrastructure - Defaults to localhost for local dev
    MONGO_URI: str = Field(default="mongodb://admin:password@localhost:27017/")
    DB_NAME: str = "sase_db"
    
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    
    SQS_ENDPOINT_URL: str = "http://localhost:4566"
    SQS_QUEUE_URL: str = "http://localhost:4566/000000000000/provisioning-queue"
    AWS_REGION: str = "us-east-1"
    
    # Feature Flags
    ENABLE_SIMULATOR: bool = True

    class Config:
        # Pydantic will read this file automatically if it exists
        env_file = ".env"
        case_sensitive = True

# Singleton instance
settings = Settings()