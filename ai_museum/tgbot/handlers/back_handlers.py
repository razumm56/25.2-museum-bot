from aiogram import F, Router, Bot, types
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command
from loguru import logger

from ai_museum.tgbot.keyboards import keyboard_choose_museums, keyboard_excursion_types


back_router = Router()

async def back_choose_excursion_types(callback: CallbackQuery):
    
    await callback.message.edit_text(
        "🎨 *Для начала выбери музей:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard_choose_museums
    )
    
async def back_personal_excursion_type(callback: CallbackQuery):
    
    await callback.message.edit_text(
        "🎯 <b>Выбери тип экскурсии:</b>\n\n"
        "🎨 <b>Персональная</b>\n"
        "Маршрут создается специально под твои интересы\n\n"
        "♾️ <b>Бесконечная</b>\n"
        "Непрерывный маршрут-квест без начала и конца\n\n"
        "📋 <b>Готовая</b>\n"
        "Проверенные маршруты по самым популярным местам",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard_excursion_types
    )
    

@back_router.callback_query(F.data == "back_choose_excursion_types")
async def process_back_choose_excursion_types(callback: CallbackQuery):
    await back_choose_excursion_types(callback=callback)
    
@back_router.callback_query(F.data == "back_personal_excursion_type")
async def process_back_personal_excursion_type(callback: CallbackQuery):
    await back_personal_excursion_type(callback=callback)
