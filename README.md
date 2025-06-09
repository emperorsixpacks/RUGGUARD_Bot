# Project RUGGUARD Bot

A Twitter bot that analyzes account trustworthiness on the Solana Network when triggered by specific phrases.

## Features

- 🔍 **Trigger Detection**: Monitors replies for "riddle me this" phrase
- 📊 **Trust Analysis**: Comprehensive account analysis including:
  - Account age and verification status
  - Follower/following ratios
  - Bio content analysis
  - Engagement patterns
  - Cross-reference with trusted accounts list
- 🤖 **Automated Responses**: Posts detailed trust reports as replies
- 🔄 **Rate Limiting**: Built-in cooldowns to prevent spam
- 🏗️ **Modular Design**: Clean, maintainable codebase

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Twitter Developer Account with API access

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/emperorsixpacks/RUGGUARD_Bot.git
cd rugguard-bot

# Install dependencies
uv sync
```

### 3. Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Fill in your Twitter API credentials in `.env`:
```
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

### 4. Running the Bot

```bash
python main.py
```

## Replit Deployment

1. Upload all files to a new Replit Python project
2. Install dependencies: `uv sync`
3. Set environment variables in Replit's Secrets tab
4. Run with: `python main.py`

## Architecture

### Core Components

- **`main.py`**: Entry point and bot lifecycle management
- **`src/bot.py`**: Main bot orchestration and logic
- **`src/twitter_client.py`**: Twitter API wrapper using Tweepy
- **`src/trust_analyzer.py`**: User trustworthiness analysis engine
- **`src/trigger_listener.py`**: Tweet monitoring and trigger detection
- **`src/models.py`**: Pydantic data models for type safety
- **`src/config.py`**: Configuration management with Pydantic Settings

### Key Features

#### Trust Analysis Metrics
- **Account Age** (0-25 points): Newer accounts score lower
- **Follower Ratio** (0-20 points): Better ratios score higher
- **Bio Analysis** (0-15 points): Keyword-based content scoring
- **Engagement Rate** (0-20 points): Based on recent tweet interactions
- **Trusted Network** (0-20 points): Connections to verified trusted accounts

#### Trigger System
- Monitors replies across Twitter for "riddle me this" phrase
- Extracts original tweet author for analysis
- Implements cooldown system to prevent spam

#### Reply Generation
- Emoji-coded trust levels (🟢🟡🟠🔴)
- Concise trust metrics summary
- Vouched status for trusted accounts
- Character limit compliance

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `TRIGGER_PHRASE` | Phrase that triggers analysis | "riddle me this" |
| `MONITOR_ACCOUNT` | Specific account to monitor (optional) | "projectrugguard" |
| `TRUST_LIST_URL` | URL for trusted accounts list | GitHub trust list |
| `ANALYSIS_COOLDOWN` | Cooldown between analyses (seconds) | 300 |

## API Usage

The bot uses Twitter API v2 with the following endpoints:
- User lookup and metrics
- Tweet search and mentions
- Tweet creation (replies)
- Follower relationships

Rate limiting is handled automatically by Tweepy.

## Error Handling

- Comprehensive logging for debugging
- Graceful degradation on API failures
- Automatic retry mechanisms for transient errors
- Rate limit compliance to prevent API suspensions

## Trust List Integration

The bot automatically fetches and updates the trusted accounts list from:
```
https://github.com/devsyrem/turst-list/blob/main/list
```

Accounts are considered vouched if:
- They appear directly on the trust list, OR
- They are followed by 2+ accounts from the trust list

## Scoring System

**Total Score: 0-100 points**

- 🟢 **80-100**: Highly Trusted
- 🟡 **60-79**: Moderately Trusted  
- 🟠 **40-59**: Neutral
- 🔴 **20-39**: Low Trust
- 🔴 **0-19**: High Risk

## Example Output

```
🟢 @example_user Trust Analysis ✅ VOUCHED

📊 Score: 87/100
📅 Account Age: 543 days
👥 Follower Ratio: 2.3
🤝 Trusted Connections: 3
✅ Established account, Good follower ratio
⚠️ No verification badge

Highly Trusted (87/100) - VOUCHED ✅
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
- Uses Pydantic for data validation
- Type hints throughout
- Comprehensive error handling
- Modular design for easy maintenance

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Troubleshooting

### Common Issues

**Bot not responding to triggers:**
- Check Twitter API credentials
- Verify bot account permissions
- Check logs for error messages
- Ensure trigger phrase is exact match

**Rate limit errors:**
- Increase cooldown periods
- Reduce API call frequency
- Check Twitter API usage limits

**Trust list not updating:**
- Verify trust list URL accessibility
- Check network connectivity
- Review logs for HTTP errors

### Support

For issues or questions:
- Check the logs first: `tail -f bot.log`
- Review Twitter API documentation
- Contact: TG @devsyrem

## License

This project is open source. Please provide proper attribution when using or modifying the code.


