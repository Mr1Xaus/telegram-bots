from aiogram import Router
from .owner import router as owner_router

def setup_admin_routers() -> Router:
    router = Router()
    router.include_router(owner_router)
    return router
