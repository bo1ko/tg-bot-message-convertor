import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from app.middlewares import DataBaseSession
from app.database import session_maker
# from app.common import private
from app.database import create_db, drop_db
from app.handlers import router

load_dotenv()


# LOGGING
logging.basicConfig(
    level=logging.INFO,  # Logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


async def on_startup(bot):
    # await drop_db()
    await create_db()


async def on_shutdown(bot):
    print("Bot down")


async def main():

    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_routers(router)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.set_my_commands(
    #     commands=private, scope=types.BotCommandScopeAllPrivateChats()
    # )
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")