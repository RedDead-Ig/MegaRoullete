import asyncio
from bot.config import TELEGRAM_BOT_TOKEN

async def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Faltou TELEGRAM_BOT_TOKEN nas variáveis de ambiente.")
    print("Boot OK. (Skeleton)")

if __name__ == "__main__":
    asyncio.run(main())
