from datetime import datetime, timedelta, timezone
from aiogram import Router, types
from aiogram.filters import Command
from bot.config import settings
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo
from bot.database.models.user import UserRoleEnum
from bot.schedulers.weekly_reset import run_weekly_reset

router = Router()

@router.message(Command("close_week", "закрыть_неделю"))
async def cmd_close_week(message: types.Message):
    if message.from_user.id != settings.owner_id and settings.owner_id != 0:
        await message.reply("⛔️ У вас нет прав Владельца для выполнения этой команды!")
        return

    await message.reply("⏳ Запускаю принудительное закрытие недели и перерасчет рангов...")
    bot = message.bot
    await run_weekly_reset(bot)
    await message.reply("✅ Неделя успешно закрыта! Ранги и статистические счетчики обновлены.")

@router.message(Command("set_role"))
async def cmd_set_role(message: types.Message):
    if message.from_user.id != settings.owner_id and settings.owner_id != 0:
        await message.reply("⛔️ У вас нет прав Владельца!")
        return

    args = message.text.split()[1:]
    if len(args) < 2:
        await message.reply("Использование: `/set_role <user_id> <USER|ADMIN_B|ADMIN_A|OWNER>`")
        return

    try:
        target_id = int(args[0])
        role_enum = UserRoleEnum(args[1].upper())
    except Exception:
        await message.reply("Некорректные аргументы.")
        return

    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(target_id)
        user.role = role_enum
        await session.commit()

    await message.reply(f"✅ Роль пользователя <code>{target_id}</code> изменена на <b>{role_enum.value}</b>", parse_mode="HTML")

@router.message(Command("grant_quota_exemption"))
async def cmd_grant_quota_exemption(message: types.Message):
    if message.from_user.id != settings.owner_id and settings.owner_id != 0:
        await message.reply("⛔️ У вас нет прав Владельца!")
        return

    args = message.text.split()[1:]
    if len(args) < 2:
        await message.reply("Использование: `/grant_quota_exemption <user_id> <days>`")
        return

    target_id = int(args[0])
    days = int(args[1])

    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(target_id)
        user.exempt_from_quota_until = datetime.now(timezone.utc) + timedelta(days=days)
        await session.commit()

    await message.reply(f"✅ Освобождение от квоты выключено на <b>{days} дней</b> для пользователя <code>{target_id}</code>", parse_mode="HTML")
