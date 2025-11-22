from aiogram import Router
from ai_museum.tgbot.handlers.start_handlers import start_router
from ai_museum.tgbot.handlers.finish_handlers import finish_router
from ai_museum.tgbot.handlers.back_handlers import back_router
from ai_museum.tgbot.handlers.personal_excursion import pers_route
from ai_museum.tgbot.handlers.infinity_excursion import inf_router
from ai_museum.tgbot.handlers.ready_excursion import router as ready_excursion_router

main_router = Router()

main_router.include_router(start_router)
main_router.include_router(finish_router)
main_router.include_router(back_router)
main_router.include_router(pers_route)
main_router.include_router(inf_router)
main_router.include_router(ready_excursion_router)
