from aiogram import Router
from .profile import router as profile_router
from .market import router as market_router

def setup_private_routers() -> Router:
    router = Router()
    router.include_router(profile_router)
    router.include_router(market_router)
    return router
