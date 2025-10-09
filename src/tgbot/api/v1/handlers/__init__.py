from aiogram import Router
from api.v1.handlers.start import start_router

main_router = Router()

main_router.include_router(start_router)