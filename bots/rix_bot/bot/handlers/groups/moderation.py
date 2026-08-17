import re
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from bot.database.session import AsyncSessionLocal
from bot.services.moderation_service import ModerationService
from bot.utils.keyboards import get_unmute_keyboard

router = Router()

def parse_duration(duration_str: str) -> int:
    """Parses 10m, 1h, 7h, 1d into seconds"""
    match = re.match(r"^(\d+)([smhd])$", duration_str.lower())
    if not match:
        return 3600  # default 1h
    val, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return val * multipliers[unit]

@router.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("⚠️ Команда должна быть ответом на сообщение пользователя!")
        return

    target = message.reply_to_message.from_user
    args = message.text.split()[1:]
    duration_str = args[0] if args else "1h"
    duration_seconds = parse_duration(duration_str)

    # Restrict permissions
    no_media = ChatPermissions(can_send_messages=False)
    try:
        await message.chat.restrict(
            user_id=target.id,
            permissions=no_media,
            until_date=duration_seconds
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка прав при муте: {e}")
        return

    async with AsyncSessionLocal() as session:
        penalty, cost = await ModerationService.apply_mute_penalty(
            session=session,
            admin_id=message.from_user.id,
            target_id=target.id,
            chat_id=message.chat.id,
            duration_seconds=duration_seconds
        )
        await session.commit()

    reply_markup = get_unmute_keyboard(target.id, duration_seconds)
    await message.answer(
        f"🤐 Пользователь <b>{target.full_name}</b> замучен на <b>{duration_str}</b>.\n"
        f"📉 Штраф репутации: <b>-{penalty} Rep</b>.\n"
        f"💸 Размут возможен за: <b>{cost} Rep</b>.",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

@router.callback_query(F.data.startswith("buy_unmute:"))
async def callback_buy_unmute(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    target_id = int(parts[1])
    duration_seconds = int(parts[2])

    if callback.from_user.id != target_id:
        await callback.answer("Вы не можете выкупить размут за другого пользователя!", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        success, msg = await ModerationService.buy_unmute(session, target_id, duration_seconds)
        if success:
            await session.commit()
            # Unrestrict user in Telegram
            try:
                full_perms = ChatPermissions(
                    can_send_messages=True,
                    can_send_other_messages=True
                )
                await callback.message.chat.restrict(user_id=target_id, permissions=full_perms)
            except Exception:
                pass

            await callback.answer("Мут снят!", show_alert=True)
            await callback.message.edit_text(f"✅ {msg}")
        else:
            await callback.answer(msg, show_alert=True)

@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("⚠️ Команда должна быть ответом на сообщение пользователя!")
        return

    target = message.reply_to_message.from_user
    try:
        await message.chat.ban(user_id=target.id)
        await message.answer(f"🚫 Пользователь <b>{target.full_name}</b> заблокирован!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка при блокировке: {e}")
