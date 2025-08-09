import logging
import sys
from pydantic_settings import BaseSettings

class LogSettings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        extra = "forbid"  # 余分なフィールドを禁止

def setup_logging():
    settings = LogSettings()
    
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    return logging.getLogger(__name__)
