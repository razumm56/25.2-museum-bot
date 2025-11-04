from aiogram import F, Router, Bot, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from loguru import logger

from tgbot.keyboards import keyboard_start_after_finish_excursion


finish_router = Router()

async def finish_excursion(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    
    logger.info(f"User {user_id} start bot")
    
    await message.answer(
        "🎨 Благодарим за участие в выставке",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard_start_after_finish_excursion
    )

@finish_router.message(F.text == "Завершить экскурсию")
async def process_finish_excursion_command(message: Message):
    await finish_excursion(message)
