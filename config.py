

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

OPENDOTA_API_URL = "https://api.opendota.com/api"
DEFAULT_DAYS = 7
TOP_HEROES_COUNT = 5

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в файле .env. ")