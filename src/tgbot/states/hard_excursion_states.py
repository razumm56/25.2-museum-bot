from aiogram.fsm.state import State, StatesGroup
from loguru import logger

class HardExcursion(StatesGroup):
    step = State()
    photo = State()
    