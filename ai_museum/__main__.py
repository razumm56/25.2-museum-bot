import asyncio
import sys

from aiogram import Bot, Dispatcher
from loguru import logger

from ai_museum.agents.infinity_excursion_agent.compiled_graphs import init_graphs
from ai_museum.db.init import init_database
from ai_museum.tgbot.handlers import main_router
from ai_museum.utils import require_env_var


async def main():
    bot = Bot(require_env_var("TELEGRAM_TOKEN"))
    dp = Dispatcher()

    await init_graphs()

    _ = dp.include_router(main_router)

    _ = await bot.delete_webhook(drop_pending_updates=True)
    try:
        print("start_polling")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(e)


if len(sys.argv) > 1 and sys.argv[1] == "init_database":
    init_database()
    sys.exit(0)

asyncio.run(main())
