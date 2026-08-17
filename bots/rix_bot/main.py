import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import settings
from bot.database.session import engine
from bot.database.models import Base
from bot.handlers import setup_all_routers
from bot.middlewares import UserChatSyncMiddleware, AntiSpamMiddleware, AntiRaidMiddleware
from bot.schedulers import run_weekly_reset, run_hourly_active_randomizer

async def main():
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )
    logging.info("Starting RiX Bot Ecosystem...")

    if settings.bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not settings.bot_token:
        logging.error("CRITICAL: Please specify a valid BOT_TOKEN in .env file!")
        sys.exit(1)

    # Initialize Database Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database tables verified/created.")

    # Initialize Redis or Fallback to MemoryStorage
    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        storage = RedisStorage(redis=redis)
        logging.info("Connected to Redis server.")
    except Exception:
        logging.warning("Redis server is not running locally. Using MemoryStorage for FSM & state caching.")
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        redis = None

    # Initialize Bot & Dispatcher
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)

    # Register Middlewares
    dp.update.outer_middleware(UserChatSyncMiddleware())
    if redis:
        dp.message.middleware(AntiSpamMiddleware(redis=redis, limit=5, period=3))
        dp.chat_member.outer_middleware(AntiRaidMiddleware(redis=redis, window_seconds=180, max_joins=10))

    # Inject Redis into handler data
    dp["redis"] = redis

    # Include All Handlers
    main_router = setup_all_routers()
    dp.include_router(main_router)

    # Setup APScheduler
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    # Weekly Reset on Mondays at 00:00 (UTC+3)
    scheduler.add_job(
        run_weekly_reset,
        trigger=CronTrigger(day_of_week="mon", hour=0, minute=0),
        args=[bot],
        id="weekly_reset_job",
        replace_existing=True
    )
    
    # Hourly Active Chatter Randomizer
    scheduler.add_job(
        run_hourly_active_randomizer,
        trigger=IntervalTrigger(hours=1),
        args=[bot],
        id="hourly_active_randomizer_job",
        replace_existing=True
    )
    
    scheduler.start()
    logging.info("APScheduler started successfully.")

    # Drop pending updates & start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("RiX Bot is running in Long Polling mode...")
    
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        if redis:
            await redis.close()
        await engine.dispose()
        logging.info("RiX Bot stopped cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Process terminated.")
