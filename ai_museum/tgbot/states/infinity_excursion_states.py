from typing import final
from aiogram.fsm.state import State, StatesGroup


@final
class InfinityExcursion(StatesGroup):
    guide_wait_user_reply = State()
    guide_chat = State()

    expert_chat = State()
