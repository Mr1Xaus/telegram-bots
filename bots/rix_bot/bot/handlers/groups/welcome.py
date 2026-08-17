import asyncio
from aiogram import Router, F, types
from aiogram.types import ChatPermissions, ChatMemberUpdated
from bot.utils.keyboards import get_join_captcha_keyboard

router = Router()

@router.chat_member(F.old_chat_member.status.in_(["left", "kicked"]), F.new_chat_member.status.in_(["member"]))
async def on_user_join(event: ChatMemberUpdated):
    user = event.new_chat_member.user
    chat = event.chat

    # Restrict new member until captcha is solved
    no_perms = ChatPermissions(can_send_messages=False)
    try:
        await chat.restrict(user_id=user.id, permissions=no_perms)
    except Exception:
        pass

    kb = get_join_captcha_keyboard(user.id)
    msg = await event.bot.send_message(
        chat_id=chat.id,
        text=(
            f"👋 Добро пожаловать, <b>{user.full_name}</b>!\n\n"
            f"Для подтверждения, что вы не бот, нажмите кнопку <b>«Я не бот»</b> ниже."
        ),
        parse_mode="HTML",
        reply_markup=kb
    )

    # Auto-delete welcome message after 5 minutes (300s)
    await asyncio.sleep(300)
    try:
        await msg.delete()
    except Exception:
        pass

@router.callback_query(F.data.startswith("captcha_verify:"))
async def callback_captcha_verify(callback: types.CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    if callback.from_user.id != target_id:
        await callback.answer("Эта кнопка не для вас!", show_alert=True)
        return

    # Unrestrict user
    full_perms = ChatPermissions(
        can_send_messages=True,
        can_send_other_messages=True,
        can_send_media_messages=True
    )
    try:
        await callback.message.chat.restrict(user_id=target_id, permissions=full_perms)
    except Exception:
        pass

    await callback.answer("Доступ открыт! Приятного общения.", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass
