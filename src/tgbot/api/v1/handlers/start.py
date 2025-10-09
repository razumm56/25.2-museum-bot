from aiogram import F, Router, Bot, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from loguru import logger


start_router = Router()


async def start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    await message.answer(
        "Давай познакомимся:\n"
        "🧠 Сколько тебе лет?\n"
        "🎨 Чем ты увлекаешься?\n"
        "💡 Что привело тебя сюда: учеба, вдохновение или просто любопытство?\n\n"
        "*Напиши* в ответ немного о себе — это поможет мне составить маршрут, который подойдёт именно тебе 😊",
        parse_mode=ParseMode.MARKDOWN
    )


@start_router.message(Command(commands=['start']))
async def process_start_command(message: Message):
    await start(message)
