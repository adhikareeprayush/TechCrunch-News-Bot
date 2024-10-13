import asyncio
import os
import logging
from datetime import datetime, timezone
from time import mktime
from dotenv import load_dotenv
import aiohttp
import feedparser
import html
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks
import uvicorn

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load bot token and chat ID from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

logger.info(f"BOT_TOKEN: {'set' if BOT_TOKEN else 'not set'}")
logger.info(f"CHAT_ID: {'set' if CHAT_ID else 'not set'}")

# Define constants
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TECHCRUNCH_RSS = 'https://techcrunch.com/feed/'

INTERESTED_CATEGORIES = {
    "AI",
    "Robotics",
    "Tech Startups",
    "Biotech & Health",
    "Enterprise",
    "Security",
    "Privacy"
}

last_sent_article_date = None

app = FastAPI()

def clean_html(raw_html):
    """Clean HTML and return text."""
    soup = BeautifulSoup(raw_html, 'html.parser')
    text = soup.get_text()
    return html.escape(text)

async def send_telegram_message(session, text):
    """Send a message to Telegram."""
    async with session.post(TELEGRAM_API_URL, json={'chat_id': CHAT_ID, 'text': text}) as response:
        return await response.json()

async def fetch_feed(session):
    """Fetch the RSS feed."""
    async with session.get(TECHCRUNCH_RSS) as response:
        return await response.text()

def get_categories(entry):
    """Extract categories from the RSS feed entry."""
    categories = set()
    for tag in entry.get('tags', []):
        if isinstance(tag, dict) and 'term' in tag:
            categories.add(clean_html(tag['term']))
    return categories

async def fetch_and_send_news(session):
    """Fetch news articles and send relevant links to Telegram."""
    global last_sent_article_date
    logger.info("Fetching news...")

    feed_content = await fetch_feed(session)
    feed = feedparser.parse(feed_content)

    if feed.entries:
        logger.info(f"Found {len(feed.entries)} entries in the feed.")
        found_interested = False

        for entry in reversed(feed.entries):  # Process entries from oldest to newest
            entry_date = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)

            if last_sent_article_date is None or entry_date > last_sent_article_date:
                categories = get_categories(entry)
                logger.info(f"Article categories: {categories}")

                if categories.intersection(INTERESTED_CATEGORIES):
                    found_interested = True
                    logger.info(f"Sending message for article: {entry.title}")
                    try:
                        response = await send_telegram_message(session, entry.link)
                        if response.get('ok'):
                            logger.info(f"Sent TechCrunch feed link: {entry.link}")
                            last_sent_article_date = entry_date
                        else:
                            logger.error(f"Failed to send message: {response}")
                    except Exception as e:
                        logger.error(f"Error sending message: {e}")
                    await asyncio.sleep(60)

        if not found_interested and last_sent_article_date is None:
            logger.info("No interested articles found. Sending fallback article.")
            for entry in reversed(feed.entries):
                entry_date = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
                try:
                    response = await send_telegram_message(session, entry.link)
                    if response.get('ok'):
                        logger.info(f"Sent fallback TechCrunch feed link: {entry.link}")
                        last_sent_article_date = entry_date
                    else:
                        logger.error(f"Failed to send fallback message: {response}")
                except Exception as e:
                    logger.error(f"Error sending fallback message: {e}")
                await asyncio.sleep(60)
                break
    else:
        logger.warning("Failed to fetch the feed or no entries found.")

async def run_bot():
    """Run the bot to periodically fetch and send news."""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await fetch_and_send_news(session)
                logger.info("Waiting for 5 minutes before next check...")
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"An error occurred in run_bot: {e}")
                await asyncio.sleep(60)  # Wait for a minute before retrying

@app.get("/")
async def root():
    """Handle root path."""
    return {"message": "TechCrunch News Bot is running"}

@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start the bot in the background."""
    background_tasks.add_task(run_bot)
    return {"message": "Bot started in the background"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('PORT', 8000)))