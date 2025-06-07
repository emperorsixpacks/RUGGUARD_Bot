"""
Project RUGGUARD Bot - File Structure and Implementation
"""

# File: main.py
import asyncio
import logging

from src.bot import RugguardBot

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Main entry point for the bot."""
    bot = RugguardBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
