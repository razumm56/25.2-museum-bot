from aiogram import Router
from tgbot.handlers.start_handlers import start_router
from tgbot.handlers.finish_handlers import finish_router
from tgbot.handlers.back_handlers import back_router
from tgbot.handlers.personal_excursion import pers_route
from tgbot.handlers.infinity_excursion import inf_router
from tgbot.handlers.ready_excursion import router as ready_excursion_router

main_router = Router()

main_router.include_router(start_router)
main_router.include_router(finish_router)
main_router.include_router(back_router)
main_router.include_router(pers_route)
main_router.include_router(inf_router)
main_router.include_router(ready_excursion_router)
