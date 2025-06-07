from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TwitterUser(BaseModel):
    """Twitter user data model."""

    id: str
    username: str
    display_name: str
    created_at: datetime
    followers_count: int
    following_count: int
    tweet_count: int
    bio: Optional[str] = None
    verified: bool = False
    profile_image_url: Optional[str] = None


class Tweet(BaseModel):
    """Twitter tweet data model."""

    id: str
    text: str
    created_at: datetime
    author_id: str
    public_metrics: Dict[str, int]
    referenced_tweets: Optional[List[Dict[str, Any]]] = None


class TrustAnalysis(BaseModel):
    """Trust analysis result model."""

    user_id: str
    username: str
    trust_score: float = Field(ge=0, le=100)
    account_age_days: int
    follower_ratio: float
    engagement_rate: float
    trusted_followers_count: int
    bio_keywords: List[str]
    red_flags: List[str]
    green_flags: List[str]
    summary: str
    is_vouched: bool = False


class BotState(BaseModel):
    """Bot state tracking model."""

    last_processed_tweet: Optional[str] = None
    processed_users: Dict[str, datetime] = Field(default_factory=dict)
    trust_list: List[str] = Field(default_factory=list)
    last_trust_list_update: Optional[datetime] = None
