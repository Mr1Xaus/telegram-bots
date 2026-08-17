from aiogram import Router
from .start import router as start_router

def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    return main_router
