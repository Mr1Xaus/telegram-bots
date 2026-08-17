from aiogram import Router
from .private import setup_private_routers
from .groups import setup_group_routers
from .admin import setup_admin_routers

def setup_all_routers() -> Router:
    main_router = Router()
    main_router.include_router(setup_private_routers())
    main_router.include_router(setup_group_routers())
    main_router.include_router(setup_admin_routers())
    return main_router
