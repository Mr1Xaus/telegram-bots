import re
from aiogram import Router, F, types
from aiogram.filters import Command
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo
from bot.services.economy_service import EconomyService

router = Router()

@router.message(F.sender_chat.not_in(None))
async def cleanup_channel_posts(message: types.Message):
    """
    Automatically delete channel posts / comments from channels
    """
    try:
        await message.delete()
    except Exception:
        pass

@router.message(F.dice)
async def cleanup_dice_emojis(message: types.Message):
    """
    Automatically delete casino/dice/rubik animated emojis
    """
    try:
        await message.delete()
    except Exception:
        pass

@router.message(Command("balance", "баланс"))
async def cmd_balance(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(message.from_user.id)
        await message.reply(f"💳 Ваш баланс репутации: <b>{user.rep_balance:.2f} Rep</b>", parse_mode="HTML")

@router.message(F.text.lower().startswith("передать"))
@router.message(Command("pay", "передать"))
async def cmd_transfer_rep(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("⚠️ Команда перевода репутации должна быть ответом на сообщение пользователя!")
        return

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    match = re.search(r"\d+(\.\d+)?", message.text)
    if not match:
        await message.reply("Укажите сумму перевода, например: `передать 50`")
        return

    amount = float(match.group(0))

    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        success, msg, net = await EconomyService.transfer_rep(user_repo, sender_id, receiver_id, amount)
        if success:
            await session.commit()
            await message.reply(f"💸 {msg}")
        else:
            await message.reply(f"❌ {msg}")
