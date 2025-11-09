from aiogram.fsm.state import State, StatesGroup

class InfinityExcursionStartup(StatesGroup):
    format = State()

class InfinityExcursionExcursion(StatesGroup):
    exhibit = State()
