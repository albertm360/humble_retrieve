from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class ScraperConfig(BaseSettings):
    """
    Strict environment variable contract.
    Fails immediately on boot if required variables are missing from .env.
    """
    # Instructs Pydantic to read from the local .env file and ignore any extra variables
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

    # Updated to match your .env file exactly
    humble_session_key: SecretStr 

    request_timeout_seconds: int = 30

    # WAF / Anti-Bot Evasion (Browser Spoofing)
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Instantiate the singleton so it reads the .env file exactly once
config = ScraperConfig() # type: ignore