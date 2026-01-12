import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ROULETTE_WS_URL     = os.getenv("ROULETTE_WS_URL", "wss://dga.pragmaticplaylive.net/ws")

CASINO_ID  = os.getenv("CASINO_ID", "ppcdk00000005349")
CURRENCY   = os.getenv("CURRENCY", "BRL")
TABLE_KEY  = int(os.getenv("TABLE_KEY", "204"))

DEFAULT_WINDOW_SIZE = int(os.getenv("DEFAULT_WINDOW_SIZE", "40"))
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # opcional (string)
