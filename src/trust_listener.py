import logging
import re
from datetime import datetime, timezone
from typing import Optional

from .config import settings
from .models import Tweet

logger = logging.getLogger(__name__)


class TriggerListener:
    """Listens for trigger phrases in tweets and mentions."""

    def __init__(self):
        self.trigger_pattern = re.compile(
            re.escape(settings.trigger_phrase), re.IGNORECASE
        )

    def is_trigger_tweet(self, tweet: Tweet) -> bool:
        """Check if a tweet contains the trigger phrase."""
        return bool(self.trigger_pattern.search(tweet.text))

    def extract_original_tweet_id(self, reply_tweet: Tweet) -> Optional[str]:
        """Extract the ID of the original tweet being replied to."""
        if not reply_tweet.referenced_tweets:
            return None

        for ref in reply_tweet.referenced_tweets:
            if ref.get("type") == "replied_to":
                return ref.get("id")

        return None

    def should_process_tweet(self, tweet: Tweet, processed_tweets: set) -> bool:
        """Determine if a tweet should be processed."""
        # Skip if already processed
        if tweet.id in processed_tweets:
            return False

        # Skip if too old (more than 1 hour)
        age = datetime.now(timezone.utc) - tweet.created_at
        if age.total_seconds() > 3600:  # 1 hour
            return False

        # Skip retweets
        if tweet.text.startswith("RT @"):
            return False

        return True
