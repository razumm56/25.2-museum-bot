from aiogram.fsm.state import State, StatesGroup


class PersonalExcursionStartup(StatesGroup):
    style = State()
    format = State()
    agent = State()


class PersonalExcursionExcursion(StatesGroup):
    exhibit = State()
