import logging
from datetime import datetime, timezone
from typing import List, Optional, Set

import requests

from .config import settings
from .models import TrustAnalysis, Tweet, TwitterUser

logger = logging.getLogger(__name__)


class TrustAnalyzer:
    """Analyzes user trustworthiness based on various metrics."""

    def __init__(self):
        self.trust_list: Set[str] = set()
        self.last_trust_list_update: Optional[datetime] = None

    async def update_trust_list(self) -> bool:
        """Update the trust list from the remote URL."""
        try:
            response = requests.get(settings.trust_list_url, timeout=10)
            response.raise_for_status()

            # Parse the trust list (assuming one username per line)
            usernames = [
                line.strip().lower()
                for line in response.text.strip().split("\n")
                if line.strip()
            ]
            self.trust_list = set(usernames)
            self.last_trust_list_update = datetime.now(timezone.utc)

            logger.info(f"Updated trust list with {len(self.trust_list)} accounts")
            return True
        except Exception as e:
            logger.error(f"Error updating trust list: {e}")
            return False

    def calculate_account_age_score(self, created_at: datetime) -> float:
        """Calculate score based on account age (0-25 points)."""
        age_days = (datetime.now(timezone.utc) - created_at).days

        if age_days < 30:
            return 0  # Very new accounts are suspicious
        elif age_days < 90:
            return 10  # Relatively new
        elif age_days < 365:
            return 20  # Established
        else:
            return 25  # Well-established

    def calculate_follower_ratio_score(self, followers: int, following: int) -> float:
        """Calculate score based on follower/following ratio (0-20 points)."""
        if following == 0:
            return 20 if followers > 0 else 0

        ratio = followers / following

        if ratio >= 2.0:
            return 20  # Good ratio
        elif ratio >= 1.0:
            return 15  # Decent ratio
        elif ratio >= 0.5:
            return 10  # Okay ratio
        elif ratio >= 0.1:
            return 5  # Poor ratio
        else:
            return 0  # Very poor ratio

    def analyze_bio_content(self, bio: str) -> tuple[List[str], float]:
        """Analyze bio content for keywords and calculate score (0-15 points)."""
        if not bio:
            return [], 0

        bio_lower = bio.lower()

        # Positive keywords
        positive_keywords = [
            "developer",
            "founder",
            "ceo",
            "official",
            "verified",
            "community",
            "building",
            "creator",
            "artist",
            "entrepreneur",
        ]

        # Negative keywords
        negative_keywords = [
            "pump",
            "moon",
            "lambo",
            "diamond hands",
            "to the moon",
            "not financial advice",
            "dyor",
            "ape",
            "100x",
            "1000x",
        ]

        found_keywords = []
        score = 5  # Base score for having a bio

        for keyword in positive_keywords:
            if keyword in bio_lower:
                found_keywords.append(f"+{keyword}")
                score += 2

        for keyword in negative_keywords:
            if keyword in bio_lower:
                found_keywords.append(f"-{keyword}")
                score -= 3

        return found_keywords, max(0, min(15, score))

    def calculate_engagement_score(self, tweets: List[Tweet], followers: int) -> float:
        """Calculate engagement score based on recent tweets (0-20 points)."""
        if not tweets or followers == 0:
            return 0

        total_engagement = 0
        for tweet in tweets:
            likes = tweet.public_metrics.get("like_count", 0)
            retweets = tweet.public_metrics.get("retweet_count", 0)
            replies = tweet.public_metrics.get("reply_count", 0)
            total_engagement += likes + retweets + replies

        avg_engagement = total_engagement / len(tweets)
        engagement_rate = (avg_engagement / followers) * 100

        if engagement_rate >= 5.0:
            return 20
        elif engagement_rate >= 2.0:
            return 15
        elif engagement_rate >= 1.0:
            return 10
        elif engagement_rate >= 0.1:
            return 5
        else:
            return 0

    async def check_trusted_followers(self, user_followers: List[str]) -> int:
        """Check how many trusted accounts follow this user."""
        if not self.trust_list:
            await self.update_trust_list()

        # Convert follower IDs to usernames (this would need additional API calls)
        # For now, we'll simulate this check
        trusted_count = 0
        # This is a simplified version - in reality you'd need to resolve IDs to usernames
        return trusted_count

    async def analyze_user(
        self, user: TwitterUser, tweets: List[Tweet], followers: List[str] = None
    ) -> TrustAnalysis:
        """Perform comprehensive trust analysis on a user."""

        # Calculate individual scores
        age_score = self.calculate_account_age_score(user.created_at)
        ratio_score = self.calculate_follower_ratio_score(
            user.followers_count, user.following_count
        )
        bio_keywords, bio_score = self.analyze_bio_content(user.bio or "")
        engagement_score = self.calculate_engagement_score(tweets, user.followers_count)

        # Check trusted followers
        trusted_followers_count = await self.check_trusted_followers(followers or [])
        trusted_score = min(
            20, trusted_followers_count * 10
        )  # 10 points per trusted follower, max 20

        # Calculate total score
        total_score = (
            age_score + ratio_score + bio_score + engagement_score + trusted_score
        )

        # Determine red and green flags
        red_flags = []
        green_flags = []

        account_age_days = (datetime.now(timezone.utc) - user.created_at).days

        if account_age_days < 30:
            red_flags.append("Very new account (less than 30 days)")
        elif account_age_days > 365:
            green_flags.append(f"Established account ({account_age_days} days old)")

        if user.followers_count / max(user.following_count, 1) < 0.1:
            red_flags.append("Poor follower/following ratio")
        elif user.followers_count / max(user.following_count, 1) > 2.0:
            green_flags.append("Good follower/following ratio")

        if user.verified:
            green_flags.append("Verified account")

        if trusted_followers_count >= 2:
            green_flags.append(
                f"Followed by {trusted_followers_count} trusted accounts"
            )

        # Check if user is on trust list
        is_vouched = (
            user.username.lower() in self.trust_list or trusted_followers_count >= 2
        )

        # Generate summary
        if total_score >= 80:
            trust_level = "Highly Trusted"
        elif total_score >= 60:
            trust_level = "Moderately Trusted"
        elif total_score >= 40:
            trust_level = "Neutral"
        elif total_score >= 20:
            trust_level = "Low Trust"
        else:
            trust_level = "High Risk"

        summary = f"{trust_level} ({total_score:.0f}/100)"
        if is_vouched:
            summary += " - VOUCHED ✅"

        return TrustAnalysis(
            user_id=user.id,
            username=user.username,
            trust_score=total_score,
            account_age_days=account_age_days,
            follower_ratio=user.followers_count / max(user.following_count, 1),
            engagement_rate=engagement_score,
            trusted_followers_count=trusted_followers_count,
            bio_keywords=bio_keywords,
            red_flags=red_flags,
            green_flags=green_flags,
            summary=summary,
            is_vouched=is_vouched,
        )
