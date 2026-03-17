"""Keroro Archive Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

# App identity
APP_NAME = "Keroro Archive"
APP_NAME_KR = "케로로 아카이브"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "케로로 군조 종합 아카이브 - 캐릭터, 에피소드, 명대사, 아이템 정보"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "keroro.db"))
WEB_DIR = os.path.join(BASE_DIR, "web")

# Server
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8002"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Rate limiting
RATE_LIMIT = os.getenv("RATE_LIMIT", "60/minute")

# Headers
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}
