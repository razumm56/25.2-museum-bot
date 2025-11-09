import asyncio

from loguru import logger

from tgbot.handlers import main_router
from loader import bot, dp


async def main():
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