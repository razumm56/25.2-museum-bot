from aiogram import F, Router, Bot, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.filters import Command
from loguru import logger

from tgbot.keyboards import keyboard_start_after_finish_excursion, choose_excursion_settings


user_input = Router()

async def procces_user_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if state_data.get('step') == "start_command":
        await message.answer("Я очень рад с вами познакомиться!🙌\n"
                            "Какой формат вам удобен?",
                            reply_markup=choose_excursion_settings)
    
    

@user_input.message()
async def process_user_input_command(message: Message, state: FSMContext):
    await procces_user_input(message=message, state=state)