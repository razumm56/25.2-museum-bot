from aiogram import Router
from tgbot.handlers.start_handlers import start_router
from tgbot.handlers.finish_handlers import finish_router
from tgbot.handlers.user_input_handlers import user_input
from tgbot.handlers.back_handlers import back_router
from tgbot.handlers.personal_excursion import personal_excursion_router

main_router = Router()

main_router.include_router(start_router)
main_router.include_router(finish_router)
main_router.include_router(back_router)
main_router.include_router(personal_excursion_router)
main_router.include_router(user_input)
