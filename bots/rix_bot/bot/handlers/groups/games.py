import random
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Rock Paper Scissors
@router.message(Command("rps", "кнб"))
async def cmd_rps(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🪨 Камень", callback_data="rps:rock"),
                InlineKeyboardButton(text="✂️ Ножницы", callback_data="rps:scissors"),
                InlineKeyboardButton(text="📜 Бумага", callback_data="rps:paper"),
            ]
        ]
    )
    await message.reply("🎮 **Камень-Ножницы-Бумага!** Сделайте ваш выбор:", reply_markup=kb)

@router.callback_query(F.data.startswith("rps:"))
async def callback_rps(callback: types.CallbackQuery):
    user_choice = callback.data.split(":")[1]
    bot_choice = random.choice(["rock", "scissors", "paper"])
    
    names = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📜 Бумага"}
    
    if user_choice == bot_choice:
        res = "🤝 Ничья!"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "scissors" and bot_choice == "paper") or \
         (user_choice == "paper" and bot_choice == "rock"):
        res = "🎉 Вы победили!"
    else:
        res = "💻 Бот победил!"

    await callback.message.edit_text(
        f"Ваш выбор: <b>{names[user_choice]}</b>\n"
        f"Выбор бота: <b>{names[bot_choice]}</b>\n\n"
        f"<b>{res}</b>",
        parse_mode="HTML"
    )
