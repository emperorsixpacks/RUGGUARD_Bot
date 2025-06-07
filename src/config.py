from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using Pydantic."""

    # Twitter API Credentials
    twitter_api_key: str = Field(..., env="TWITTER_API_KEY")
    twitter_api_secret: str = Field(..., env="TWITTER_API_SECRET")
    twitter_access_token: str = Field(..., env="TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: str = Field(..., env="TWITTER_ACCESS_TOKEN_SECRET")
    twitter_bearer_token: str = Field(..., env="TWITTER_BEARER_TOKEN")

    # Bot Configuration
    trigger_phrase: str = Field("riddle me this", env="TRIGGER_PHRASE")
    monitor_account: Optional[str] = Field("projectrugguard", env="MONITOR_ACCOUNT")
    trust_list_url: str = Field(
        "https://raw.githubusercontent.com/devsyrem/turst-list/refs/heads/main/list",
        env="TRUST_LIST_URL",
    )

    # Rate limiting
    analysis_cooldown: int = Field(300, env="ANALYSIS_COOLDOWN")  # 5 minutes

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
