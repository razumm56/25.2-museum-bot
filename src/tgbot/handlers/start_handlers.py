from aiogram import F, Router, Bot, types
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from tgbot.keyboards import keyboard_choose_museums, keyboard_excursion_types, keyboard_after_choose_personal_excursion_type
from tgbot.states import HardExcursion, Start

start_router = Router()

async def start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    
    await state.set_state(Start.step)
    await state.update_data(step="start")
    
    logger.info(f"User {user_id} @{username} start bot")

    await message.answer(
        "👋 Привет! Добро пожаловать в бот-гид по музеям!\n\n"
        "Я создан, чтобы помочь тебе познакомиться с искусством и найти то, что действительно затронет твою душу. "
        "Вместо скучных экскурсий я предлагаю персонализированные маршруты, которые соответствуют твоим интересам.\n\n",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await message.answer(
        "🎨 *Для начала выбери музей:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard_choose_museums
    )
    
async def choose_type_excursion(callback: CallbackQuery, state: FSMContext):
    
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

@start_router.message(Command(commands=['start']))
async def process_start_command(message: Message, state: FSMContext):
    await start(message=message, state=state)
    
@start_router.message(F.text == "Начать заново")
async def process_start_again_command(message: Message, state: FSMContext):
    await state.clear()
    await start(message=message, state=state)
    
@start_router.callback_query(F.data.startswith("choosed_museum_"))
async def process_choose_type_excursion(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.message.from_user.id} choosing excursion type")
    await choose_type_excursion(callback=callback, state=state)
