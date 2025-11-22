from aiogram import Bot, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from ai_museum.tgbot.keyboards import keyboard_start_after_finish_excursion

finish_router = Router()

async def finish_excursion(message: types.Message | types.CallbackQuery, bot: Bot):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    
    logger.info(f"User {user_id} @{username} start bot")

    await bot.send_message(user_id,
        "🎨 Благодарим за участие в выставке",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard_start_after_finish_excursion
    )

@finish_router.message(F.text == "Завершить экскурсию")
async def process_finish_excursion_command(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await finish_excursion(message, bot)
