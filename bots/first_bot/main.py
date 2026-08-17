import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import settings
from handlers import setup_routers

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )
    logging.info("Инициализация бота...")

    if settings.bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not settings.bot_token:
        logging.error("ОШИБКА: Пожалуйста, укажите реальный BOT_TOKEN в файле .env!")
        sys.exit(1)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Регистрация роутеров
    main_router = setup_routers()
    dp.include_router(main_router)

    # Пропуск накопившихся апдейтов перед запуском
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("Бот успешно запущен (Long Polling)...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
