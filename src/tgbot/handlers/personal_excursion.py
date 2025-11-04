import time

from aiogram import F, Router, Bot, types
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command
from loguru import logger

from tgbot.keyboards import keyboard_choose_museums, keyboard_excursion_types


personal_excursion_router = Router()

async def excursion_with_photo(callback: CallbackQuery):
    
    await callback.message.edit_text(
        "Подождите немного, я готовлю ваш маршрут... ⏳",
    )
    
    time.sleep(5)
    
    await callback.message.edit_text(
        "1. Тест\n",
        "2. Тест\n",
        "3. Тест",
    )
    
    await callback.message.answer(
        "Карта вашего маршрута"
    )
    
    await callback.message.answer(
        "Вы готовы начать экскурсию?"
    )
    

@personal_excursion_router.callback_query(F.data == "excursion_with_photo_pressed")
async def process_excursion_with_photo(callback: CallbackQuery):
    await excursion_with_photo(callback=callback)