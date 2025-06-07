import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Set

from .config import settings
from .models import BotState
from .trigger_listener import TriggerListener
from .trust_analyzer import TrustAnalyzer
from .twitter_client import TwitterClient

logger = logging.getLogger(__name__)


class RugguardBot:
    """Main bot class that orchestrates all components."""

    def __init__(self):
        self.twitter_client = TwitterClient()
        self.trust_analyzer = TrustAnalyzer()
        self.trigger_listener = TriggerListener()
        self.state = BotState()
        self.processed_tweets: Set[str] = set()
        self.running = False

    async def start(self):
        """Start the bot."""
        logger.info("Starting RUGGUARD Bot...")
        self.running = True

        # Update trust list on startup
        await self.trust_analyzer.update_trust_list()

        # Main bot loop
        while self.running:
            try:
                await self.process_mentions()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping RUGGUARD Bot...")
        self.running = False

    async def process_mentions(self):
        """Process recent mentions for trigger phrases."""
        try:
            mentions = await self.twitter_client.get_mentions(max_results=20)

            for mention in mentions:
                if not self.trigger_listener.should_process_tweet(
                    mention, self.processed_tweets
                ):
                    continue

                if self.trigger_listener.is_trigger_tweet(mention):
                    await self.handle_trigger(mention)
                    self.processed_tweets.add(mention.id)

        except Exception as e:
            logger.error(f"Error processing mentions: {e}")

    async def handle_trigger(self, trigger_tweet):
        """Handle a trigger phrase detection."""
        logger.info(f"Trigger detected in tweet {trigger_tweet.id}")

        # Extract original tweet ID
        original_tweet_id = self.trigger_listener.extract_original_tweet_id(
            trigger_tweet
        )
        if not original_tweet_id:
            logger.warning(f"Could not find original tweet for {trigger_tweet.id}")
            return

        try:
            # Get original tweet to find author
            original_tweet_response = self.twitter_client.client.get_tweet(
                original_tweet_id, expansions=["author_id"]
            )

            if not original_tweet_response.data:
                logger.warning(f"Could not fetch original tweet {original_tweet_id}")
                return

            author_id = str(original_tweet_response.data.author_id)

            # Check cooldown
            if self.is_user_on_cooldown(author_id):
                logger.info(f"User {author_id} is on cooldown, skipping analysis")
                return

            # Perform analysis
            analysis_result = await self.analyze_user(author_id)
            if analysis_result:
                # Generate and post reply
                reply_text = self.generate_reply(analysis_result)
                success = await self.twitter_client.reply_to_tweet(
                    trigger_tweet.id, reply_text
                )

                if success:
                    logger.info(
                        f"Successfully replied to trigger tweet {trigger_tweet.id}"
                    )
                    self.state.processed_users[author_id] = datetime.now(timezone.utc)
                else:
                    logger.error(f"Failed to reply to trigger tweet {trigger_tweet.id}")

        except Exception as e:
            logger.error(f"Error handling trigger: {e}")

    def is_user_on_cooldown(self, user_id: str) -> bool:
        """Check if user analysis is on cooldown."""
        if user_id not in self.state.processed_users:
            return False

        last_processed = self.state.processed_users[user_id]
        cooldown_end = last_processed + timedelta(seconds=settings.analysis_cooldown)
        return datetime.now(timezone.utc) < cooldown_end

    async def analyze_user(self, user_id: str):
        """Perform complete user analysis."""
        try:
            # Get user information
            user = await self.twitter_client.get_user_by_id(user_id)
            if not user:
                logger.error(f"Could not fetch user {user_id}")
                return None

            # Get user tweets
            tweets = await self.twitter_client.get_user_tweets(user_id, max_results=10)

            # Get followers (limited to avoid rate limits)
            followers = await self.twitter_client.get_followers(
                user_id, max_results=100
            )

            # Perform trust analysis
            analysis = await self.trust_analyzer.analyze_user(user, tweets, followers)

            logger.info(
                f"Analysis complete for @{user.username}: {analysis.trust_score:.1f}/100"
            )
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing user {user_id}: {e}")
            return None

    def generate_reply(self, analysis) -> str:
        """Generate a reply tweet based on analysis results."""

        # Emoji based on trust score
        if analysis.trust_score >= 80:
            emoji = "🟢"
        elif analysis.trust_score >= 60:
            emoji = "🟡"
        elif analysis.trust_score >= 40:
            emoji = "🟠"
        else:
            emoji = "🔴"

        vouched_status = "✅ VOUCHED" if analysis.is_vouched else ""

        reply = f"{emoji} @{analysis.username} Trust Analysis {vouched_status}\n\n"
        reply += f"📊 Score: {analysis.trust_score:.0f}/100\n"
        reply += f"📅 Account Age: {analysis.account_age_days} days\n"
        reply += f"👥 Follower Ratio: {analysis.follower_ratio:.1f}\n"

        if analysis.trusted_followers_count > 0:
            reply += f"🤝 Trusted Connections: {analysis.trusted_followers_count}\n"

        if analysis.green_flags:
            reply += f"✅ {', '.join(analysis.green_flags[:2])}\n"

        if analysis.red_flags:
            reply += f"⚠️ {', '.join(analysis.red_flags[:2])}\n"

        reply += f"\n{analysis.summary}"

        # Ensure tweet is under character limit
        if len(reply) > 280:
            reply = reply[:275] + "..."

        return reply
