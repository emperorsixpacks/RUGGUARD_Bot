from datetime import datetime, timedelta, timezone

import pytest

from src.models import Tweet, TwitterUser
from src.trust_analyzer import TrustAnalyzer


@pytest.fixture
def trust_analyzer():
    return TrustAnalyzer()


@pytest.fixture
def sample_user():
    return TwitterUser(
        id="123456789",
        username="testuser",
        display_name="Test User",
        created_at=datetime.now(timezone.utc) - timedelta(days=365),
        followers_count=1000,
        following_count=500,
        tweet_count=2500,
        bio="Developer and blockchain enthusiast",
        verified=False,
    )


@pytest.fixture
def sample_tweets():
    return [
        Tweet(
            id="1",
            text="Just launched my new project!",
            created_at=datetime.now(timezone.utc),
            author_id="123456789",
            public_metrics={"like_count": 50, "retweet_count": 10, "reply_count": 5},
        ),
        Tweet(
            id="2",
            text="Working on some cool features",
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            author_id="123456789",
            public_metrics={"like_count": 25, "retweet_count": 5, "reply_count": 3},
        ),
    ]


def test_calculate_account_age_score(trust_analyzer):
    # Test very new account
    new_date = datetime.now(timezone.utc) - timedelta(days=15)
    assert trust_analyzer.calculate_account_age_score(new_date) == 0

    # Test established account
    old_date = datetime.now(timezone.utc) - timedelta(days=400)
    assert trust_analyzer.calculate_account_age_score(old_date) == 25


def test_calculate_follower_ratio_score(trust_analyzer):
    # Test good ratio
    assert trust_analyzer.calculate_follower_ratio_score(2000, 1000) == 20

    # Test poor ratio
    assert trust_analyzer.calculate_follower_ratio_score(100, 2000) == 0


def test_analyze_bio_content(trust_analyzer):
    # Test positive bio
    keywords, score = trust_analyzer.analyze_bio_content(
        "Blockchain developer and founder"
    )
    assert score > 5
    assert any("developer" in k for k in keywords)

    # Test negative bio
    keywords, score = trust_analyzer.analyze_bio_content(
        "Going to the moon! 100x gains!"
    )
    assert score < 5


@pytest.mark.asyncio
async def test_analyze_user(trust_analyzer, sample_user, sample_tweets):
    analysis = await trust_analyzer.analyze_user(sample_user, sample_tweets)

    assert analysis.user_id == "123456789"
    assert analysis.username == "testuser"
    assert 0 <= analysis.trust_score <= 100
    assert analysis.account_age_days > 0
    assert analysis.follower_ratio > 0


from datetime import datetime, timedelta, timezone

# File: tests/test_trigger_listener.py
import pytest

from src.models import Tweet
from src.trigger_listener import TriggerListener


@pytest.fixture
def trigger_listener():
    return TriggerListener()


@pytest.fixture
def trigger_tweet():
    return Tweet(
        id="123",
        text="@projectrugguard riddle me this about this account",
        created_at=datetime.now(timezone.utc),
        author_id="456",
        public_metrics={"like_count": 0, "retweet_count": 0, "reply_count": 0},
        referenced_tweets=[{"type": "replied_to", "id": "789"}],
    )


@pytest.fixture
def non_trigger_tweet():
    return Tweet(
        id="124",
        text="Just a regular tweet here",
        created_at=datetime.now(timezone.utc),
        author_id="456",
        public_metrics={"like_count": 0, "retweet_count": 0, "reply_count": 0},
    )


def test_is_trigger_tweet(trigger_listener, trigger_tweet, non_trigger_tweet):
    assert trigger_listener.is_trigger_tweet(trigger_tweet) == True
    assert trigger_listener.is_trigger_tweet(non_trigger_tweet) == False


def test_extract_original_tweet_id(trigger_listener, trigger_tweet):
    original_id = trigger_listener.extract_original_tweet_id(trigger_tweet)
    assert original_id == "789"


def test_should_process_tweet(trigger_listener, trigger_tweet):
    processed_tweets = set()

    # Should process new tweet
    assert (
        trigger_listener.should_process_tweet(trigger_tweet, processed_tweets) == True
    )

    # Should not process already processed tweet
    processed_tweets.add(trigger_tweet.id)
    assert (
        trigger_listener.should_process_tweet(trigger_tweet, processed_tweets) == False
    )

    # Should not process old tweet
    old_tweet = Tweet(
        id="125",
        text="Old tweet",
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
        author_id="456",
        public_metrics={"like_count": 0, "retweet_count": 0, "reply_count": 0},
    )
    assert trigger_listener.should_process_tweet(old_tweet, set()) == False
