from aiogram.fsm.state import State, StatesGroup

class InfinityExcursionStartup(StatesGroup):
    format = State()

class InfinityExcursion(StatesGroup):
    exhibit = State()
    fff = State()
