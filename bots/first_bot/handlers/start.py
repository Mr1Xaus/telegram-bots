from aiogram import Router, types
from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    """
    user_name = message.from_user.full_name if message.from_user else "пользователь"
    await message.answer(
        f"👋 Привет, <b>{user_name}</b>!\n\n"
        f"Я твой новый Telegram-бот на базе <b>aiogram 3</b>.\n"
        f"Отправь мне любое сообщение, и я отвечу эхом, или используй /help.",
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Обработчик команды /help
    """
    await message.answer(
        "🛠 <b>Справка по боту:</b>\n"
        "• /start — Перезапустить бота\n"
        "• /help — Показать эту справку\n"
        "• Текст — Эхо-ответ на любое текстовое сообщение",
        parse_mode="HTML"
    )

@router.message()
async def echo_handler(message: types.Message):
    """
    Обработчик всех остальных текстовых сообщений (эхо)
    """
    if message.text:
        await message.answer(f"Вы написали: {message.text}")
