import os
from dotenv import load_dotenv

# Load environment variables from .env file, overriding existing vars
load_dotenv(override=True)

class Config:
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Telegram Settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Email Settings
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
    
    # Database Settings
    CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    
    # RSS Feeds List
    FINANCE_RSS_FEEDS = [
        "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.livemint.com/rss/markets",
        # Add more reliable feeds here
    ]

    # Content Thresholds
    SIMILARITY_THRESHOLD = 0.85 # Above this, it's considered duplicate
    MINIMUM_SIGNAL_SCORE = 24 # Out of 30, minimum score to proceed to generation
