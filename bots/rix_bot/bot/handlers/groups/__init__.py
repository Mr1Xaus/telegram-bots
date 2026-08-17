from aiogram import Router
from .moderation import router as moderation_router
from .economy import router as economy_router
from .marriage import router as marriage_router
from .games import router as games_router
from .welcome import router as welcome_router
from .clans_handler import router as clans_router
from .chat_management import router as chat_management_router

def setup_group_routers() -> Router:
    router = Router()
    router.include_router(moderation_router)
    router.include_router(economy_router)
    router.include_router(marriage_router)
    router.include_router(games_router)
    router.include_router(welcome_router)
    router.include_router(clans_router)
    router.include_router(chat_management_router)
    return router
