from aiogram import Router
from .start_handlers import start_router
from .finish_handlers import finish_router
from .back_handlers import back_router
from .personal_excursion import pers_route
from .infinity_excursion import inf_router
from .ready_excursion import router as ready_excursion_router

main_router = Router()

main_router.include_router(start_router)
main_router.include_router(finish_router)
main_router.include_router(back_router)
main_router.include_router(pers_route)
main_router.include_router(inf_router)
main_router.include_router(ready_excursion_router)
