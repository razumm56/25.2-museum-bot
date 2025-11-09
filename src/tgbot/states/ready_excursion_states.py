from aiogram.fsm.state import State, StatesGroup


class ReadyExcursionStartup(StatesGroup):
    style = State()
    format = State()


class ReadyExcursionExcursion(StatesGroup):
    exhibit = State()
