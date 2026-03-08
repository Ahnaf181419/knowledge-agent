import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

WEBSCRAPING_API_KEY = os.getenv("WEBSCRAPING_API_KEY", "")
