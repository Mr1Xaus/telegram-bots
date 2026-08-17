import random
import time
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from redis.asyncio import Redis
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo

router = Router()

@router.message(F.text.lower().startswith("пощёчина"))
@router.message(Command("slap", "пощёчина"))
async def cmd_slap(message: types.Message, redis: Redis):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("⚠️ Команда «Пощёчина» должна быть ответом на сообщение пользователя!")
        return

    sender_id = message.from_user.id
    target = message.reply_to_message.from_user

    if sender_id == target.id:
        await message.reply("Нельзя дать пощёчину самому себе!")
        return

    # Check cooldown (10 minutes = 600s)
    if redis:
        cd_key = f"slap_cd:{sender_id}"
        ttl = await redis.ttl(cd_key)
        if ttl > 0:
            await message.reply(f"⏳ Кулдаун пощёчины noch {ttl} сек.")
            return

    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        success = await user_repo.deduct_rep(sender_id, 15.0)
        if not success:
            await message.reply("Недостаточно репутации! Стоимость пощёчины: 15 Rep.")
            return
        await session.commit()

    if redis:
        await redis.setex(f"slap_cd:{sender_id}", 600, int(time.time()))
        await redis.setex(f"slapped_by:{target.id}", 3600, sender_id)

    # Mute target for 2 minutes (120s)
    try:
        no_perms = ChatPermissions(can_send_messages=False)
        await message.chat.restrict(user_id=target.id, permissions=no_perms, until_date=120)
    except Exception:
        pass

    await message.reply(
        f"👋 <b>{message.from_user.full_name}</b> дал звонкую пощёчину <b>{target.full_name}</b>!\n"
        f"🤫 Жертва получает мут на 2 минуты (-15 Rep у нападавшего).",
        parse_mode="HTML"
    )

@router.message(Command("counter_attack", "контр_атака"))
async def cmd_counter_attack(message: types.Message, redis: Redis):
    if not redis:
        await message.reply("Контр атака временно недоступна без Redis.")
        return

    target_id = message.from_user.id
    attacker_id_bytes = await redis.get(f"slapped_by:{target_id}")
    if not attacker_id_bytes:
        await message.reply("Вас недавно никто не давал пощёчину для контр атаки!")
        return

    attacker_id = int(attacker_id_bytes.decode())
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        success = await user_repo.deduct_rep(target_id, 15.0)
        if not success:
            await message.reply("Недостаточно репутации для контр атаки (15 Rep)!")
            return
        await session.commit()

    # Mute attacker for 3 minutes (180s)
    try:
        no_perms = ChatPermissions(can_send_messages=False)
        await message.chat.restrict(user_id=attacker_id, permissions=no_perms, until_date=180)
    except Exception:
        pass

    await message.reply(
        f"💥 <b>{message.from_user.full_name}</b> провел успешную <b>Контр Атаку</b>!\n"
        f"🤫 Нападавший <code>{attacker_id}</code> отправлен в мут на 3 минуты!",
        parse_mode="HTML"
    )

@router.message(Command("rps", "цуефа", "кнб"))
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
    await message.reply("🎮 <b>Камень-Ножницы-Бумага (Цуефа)!</b> Сделайте ваш выбор:", parse_mode="HTML", reply_markup=kb)

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
        res = "💻 Бот победил! Вы получаете мут на 1 минуту."
        try:
            no_perms = ChatPermissions(can_send_messages=False)
            await callback.message.chat.restrict(user_id=callback.from_user.id, permissions=no_perms, until_date=60)
        except Exception:
            pass

    await callback.message.edit_text(
        f"Ваш выбор: <b>{names[user_choice]}</b>\n"
        f"Выбор бота: <b>{names[bot_choice]}</b>\n\n"
        f"<b>{res}</b>",
        parse_mode="HTML"
    )
