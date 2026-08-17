from aiogram import Router, F, types
from aiogram.filters import Command
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.clan_repo import ClanRepo
from bot.services.clan_service import ClanService

router = Router()

@router.message(F.text.lower().startswith("!создать клан"))
@router.message(Command("create_clan", "создать_клан"))
async def cmd_create_clan(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Укажите название клана, например: `!создать клан Орден`")
        return

    clan_name = parts[1].strip()
    async with AsyncSessionLocal() as session:
        success, msg = await ClanService.create_clan(session, message.from_user.id, clan_name)
        if success:
            await session.commit()
            await message.reply(f"🎉 {msg}", parse_mode="HTML")
        else:
            await message.reply(f"❌ {msg}")

@router.message(F.text.lower().startswith("мой клан"))
@router.message(Command("my_clan", "мой_клан"))
async def cmd_my_clan(message: types.Message):
    async with AsyncSessionLocal() as session:
        clan_repo = ClanRepo(session)
        clan = await clan_repo.get_user_clan(message.from_user.id)

        if not clan:
            await message.reply("Вы не состоите ни в одном клане! Создайте свой через `!создать клан [название]` (1500 Rep).")
            return

        count = await clan_repo.get_member_count(clan.id)
        text = (
            f"🏰 <b>Клан «{clan.name}»</b>\n\n"
            f"👑 Владелец ID: <code>{clan.owner_id}</code>\n"
            f"👥 Участники: <b>{count}/{clan.max_slots}</b>\n"
            f"🌾 Нафармлено репутации: <b>{clan.total_farmed_rep:.2f} Rep</b>\n"
        )
        await message.reply(text, parse_mode="HTML")

@router.message(F.text.lower().startswith("расформировать клан"))
@router.message(Command("disband_clan"))
async def cmd_disband_clan(message: types.Message):
    async with AsyncSessionLocal() as session:
        success, msg = await ClanService.disband_clan(session, message.from_user.id)
        if success:
            await session.commit()
            await message.reply(f"✅ {msg}")
        else:
            await message.reply(f"❌ {msg}")
