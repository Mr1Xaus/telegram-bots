from aiogram import Router, F, types
from aiogram.filters import Command
from redis.asyncio import Redis
from bot.database.session import AsyncSessionLocal
from bot.services.marriage_service import MarriageService
from bot.utils.keyboards import get_marriage_proposal_keyboard

router = Router()

@router.message(F.text.lower().startswith("брак"))
@router.message(Command("marriage", "брак"))
async def cmd_marriage_propose(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("⚠️ Команда заключения брака должна быть ответом на сообщение любимого человека!")
        return

    proposer = message.from_user
    partner = message.reply_to_message.from_user

    if proposer.id == partner.id:
        await message.reply("Нельзя вступить в брак с самим собой!")
        return

    reply_markup = get_marriage_proposal_keyboard(proposer.id)
    await message.reply(
        f"💍 <b>{proposer.full_name}</b> делает предложение руки и сердца <b>{partner.full_name}</b>!\n"
        f"Вы согласны вступить в брак?",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

@router.callback_query(F.data.startswith("marriage_accept:"))
async def callback_marriage_accept(callback: types.CallbackQuery):
    proposer_id = int(callback.data.split(":")[1])
    partner_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        success, msg = await MarriageService.propose_marriage(session, proposer_id, partner_id)
        if success:
            await session.commit()
            await callback.answer("Поздравляем!", show_alert=True)
            await callback.message.edit_text(f"🎉 {msg}")
        else:
            await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("marriage_reject:"))
async def callback_marriage_reject(callback: types.CallbackQuery):
    await callback.answer("Предложение отклонено.")
    await callback.message.edit_text("💔 Предложение руки и сердца было отклонено...")

@router.message(Command("kiss", "поцеловать"))
async def cmd_kiss(message: types.Message, redis: Redis):
    if not message.reply_to_message:
        return
    success, msg = await MarriageService.interact(
        redis=redis,
        action="kiss",
        user_id=message.from_user.id,
        partner_id=message.reply_to_message.from_user.id
    )
    await message.reply(msg)

@router.message(Command("sleep", "переспать"))
async def cmd_sleep(message: types.Message, redis: Redis):
    if not message.reply_to_message:
        return
    success, msg = await MarriageService.interact(
        redis=redis,
        action="sleep",
        user_id=message.from_user.id,
        partner_id=message.reply_to_message.from_user.id
    )
    await message.reply(msg)

@router.message(Command("date", "свидание"))
async def cmd_date(message: types.Message, redis: Redis):
    if not message.reply_to_message:
        return
    success, msg = await MarriageService.interact(
        redis=redis,
        action="date",
        user_id=message.from_user.id,
        partner_id=message.reply_to_message.from_user.id
    )
    await message.reply(msg)
