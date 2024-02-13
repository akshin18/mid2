import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


MIDJOURNERY_ID = 936929561302675456
SESSION_ID = "anything"
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
HEADERS = {
        "Authorization": AUTH_TOKEN,
    }

PROMPT_GENERATE_TYPE = ["(relaxed)"]
UPSCALE_TYPE = ["(Creative)","(Subtle)"]