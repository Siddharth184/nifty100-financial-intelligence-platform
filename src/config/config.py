"""
Configuration module for Nifty100 Financial Intelligence Platform.
Reads environment variables from .env file and provides structured configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Define base directory of the project (2 levels up from src/config/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file located at the project root
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    """Application Configuration class."""
    
    # Application identity
    APP_NAME: str = os.getenv("APP_NAME", "Nifty100 Financial Intelligence Platform")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db' / 'nifty100.db'}")
    DB_PATH: Path = BASE_DIR / os.getenv("DB_PATH", "db/nifty100.db")
    DB_SCHEMA_PATH: Path = BASE_DIR / os.getenv("DB_SCHEMA_PATH", "db/schema.sql")

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = BASE_DIR / os.getenv("LOG_DIR", "logs")
    LOG_FILE: Path = BASE_DIR / os.getenv("LOG_FILE", "logs/app.log")

    # Data directory paths
    DATA_RAW_DIR: Path = BASE_DIR / os.getenv("DATA_RAW_DIR", "data/raw")
    DATA_PROCESSED_DIR: Path = BASE_DIR / os.getenv("DATA_PROCESSED_DIR", "data/processed")
    DATA_BACKUP_DIR: Path = BASE_DIR / os.getenv("DATA_BACKUP_DIR", "data/backup")
    OUTPUT_DIR: Path = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
    REPORTS_DIR: Path = BASE_DIR / os.getenv("REPORTS_DIR", "reports")

    @classmethod
    def ensure_directories(cls):
        """Create necessary project directories if they do not exist."""
        for dir_path in [
            cls.LOG_DIR,
            cls.DATA_RAW_DIR,
            cls.DATA_PROCESSED_DIR,
            cls.DATA_BACKUP_DIR,
            cls.OUTPUT_DIR,
            cls.REPORTS_DIR,
            cls.DB_PATH.parent,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

def load_config() -> Config:
    """Helper function to load config and ensure required directory paths exist."""
    config = Config()
    config.ensure_directories()
    return config

if __name__ == "__main__":
    cfg = load_config()
    print(f"Loaded config for: {cfg.APP_NAME}")
    print(f"Database Path: {cfg.DB_PATH}")
    print(f"Log Level: {cfg.LOG_LEVEL}")
