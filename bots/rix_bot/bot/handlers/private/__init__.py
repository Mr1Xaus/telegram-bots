from aiogram import Router
from .profile import router as profile_router
from .market import router as market_router
from .pm_menu import router as pm_menu_router

def setup_private_routers() -> Router:
    router = Router()
    router.include_router(profile_router)
    router.include_router(market_router)
    router.include_router(pm_menu_router)
    return router
