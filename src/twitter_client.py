import logging
from typing import List, Optional

import tweepy

from .config import settings
from .models import Tweet, TwitterUser

logger = logging.getLogger(__name__)


class TwitterClient:
    """Twitter API client wrapper."""

    def __init__(self):
        """Initialize Twitter client with API credentials."""
        self.client = tweepy.Client(
            bearer_token=settings.twitter_bearer_token,
            consumer_key=settings.twitter_api_key,
            consumer_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )

        # API v1.1 for additional features
        auth = tweepy.OAuth1UserHandler(
            settings.twitter_api_key,
            settings.twitter_api_secret,
            settings.twitter_access_token,
            settings.twitter_access_token_secret,
        )
        self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

    async def get_user_by_id(self, user_id: str) -> Optional[TwitterUser]:
        """Get user information by ID."""
        try:
            response = self.client.get_user(
                id=user_id,
                user_fields=[
                    "created_at",
                    "description",
                    "public_metrics",
                    "verified",
                    "profile_image_url",
                ],
            )

            if response.data:
                user_data = response.data
                return TwitterUser(
                    id=str(user_data.id),
                    username=user_data.username,
                    display_name=user_data.name,
                    created_at=user_data.created_at,
                    followers_count=user_data.public_metrics["followers_count"],
                    following_count=user_data.public_metrics["following_count"],
                    tweet_count=user_data.public_metrics["tweet_count"],
                    bio=user_data.description,
                    verified=user_data.verified or False,
                    profile_image_url=user_data.profile_image_url,
                )
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
        return None

    async def get_user_tweets(self, user_id: str, max_results: int = 10) -> List[Tweet]:
        """Get recent tweets from a user."""
        try:
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics", "referenced_tweets"],
            )

            tweets = []
            if response.data:
                for tweet_data in response.data:
                    tweets.append(
                        Tweet(
                            id=str(tweet_data.id),
                            text=tweet_data.text,
                            created_at=tweet_data.created_at,
                            author_id=str(tweet_data.author_id),
                            public_metrics=tweet_data.public_metrics,
                            referenced_tweets=tweet_data.referenced_tweets,
                        )
                    )
            return tweets
        except Exception as e:
            logger.error(f"Error fetching tweets for user {user_id}: {e}")
            return []

    async def get_mentions(self, max_results: int = 10) -> List[Tweet]:
        """Get recent mentions."""
        try:
            response = self.client.get_users_mentions(
                id=self.client.get_me().data.id,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics", "referenced_tweets"],
                expansions=["author_id", "referenced_tweets.id"],
            )

            tweets = []
            if response.data:
                for tweet_data in response.data:
                    tweets.append(
                        Tweet(
                            id=str(tweet_data.id),
                            text=tweet_data.text,
                            created_at=tweet_data.created_at,
                            author_id=str(tweet_data.author_id),
                            public_metrics=tweet_data.public_metrics,
                            referenced_tweets=tweet_data.referenced_tweets,
                        )
                    )
            return tweets
        except Exception as e:
            logger.error(f"Error fetching mentions: {e}")
            return []

    async def reply_to_tweet(self, tweet_id: str, text: str) -> bool:
        """Reply to a tweet."""
        try:
            response = self.client.create_tweet(
                text=text, in_reply_to_tweet_id=tweet_id
            )
            return response.data is not None
        except Exception as e:
            logger.error(f"Error replying to tweet {tweet_id}: {e}")
            return False

    async def get_followers(self, user_id: str, max_results: int = 1000) -> List[str]:
        """Get follower IDs for a user."""
        try:
            followers = []
            for page in tweepy.Paginator(
                self.client.get_users_followers,
                id=user_id,
                max_results=min(max_results, 1000),
                limit=1,
            ):
                if page.data:
                    followers.extend([str(user.id) for user in page.data])
            return followers
        except Exception as e:
            logger.error(f"Error fetching followers for user {user_id}: {e}")
            return []
