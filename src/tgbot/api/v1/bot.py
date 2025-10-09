import asyncio
import os

from aiogram import Bot, Dispatcher
from loguru import logger
from dotenv import load_dotenv

from api.v1.handlers import main_router

load_dotenv()


async def main():

    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    dp = Dispatcher()

    # Регистрация routers
    dp.include_router(main_router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await asyncio.gather(
            dp.start_polling(
                bot
            )
        )
    except Exception as e:
        logger.exception(e)