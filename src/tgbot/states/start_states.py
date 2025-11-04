from aiogram.fsm.state import State, StatesGroup
from loguru import logger

class Start(StatesGroup):
    step = State()