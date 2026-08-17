from aiogram import Router, F, types
from aiogram.filters import Command
from bot.config import settings
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo
from bot.database.models.user import GenderEnum, UserRoleEnum
from bot.utils.keyboards import get_main_pm_keyboard

router = Router()

LEVEL_COSTS = {
    0: 1500.0,
    1: 3500.0,
    2: 7500.0,
    3: 15000.0,
    4: 25000.0,
}

@router.message(F.text.lower().in_(["кто я", "кто ты", "мой профиль"]))
@router.message(Command("whoami", "whois"))
async def cmd_whoami(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(target.id)

        gender_str = {
            GenderEnum.MALE: "👨 Мужской",
            GenderEnum.FEMALE: "👩 Женский",
            GenderEnum.UNKNOWN: "❓ Не указан"
        }.get(user.gender, "❓ Не указан")

        text = (
            f"👤 <b>Пользователь:</b> {target.full_name}\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"🎭 Роль: <b>{user.role.value}</b>\n"
            f"⭐ Уровень: <b>Участник [{user.level}]</b> (+{user.level * 0.2:.1f}x)\n"
            f"💰 Баланс: <b>{user.rep_balance:.2f} Rep</b>\n"
            f"⚧ Пол: <b>{gender_str}</b>\n"
        )
        await message.reply(text, parse_mode="HTML")

@router.message(F.text.lower().in_(["кто админ", "созвать админов"]))
@router.message(Command("admins", "кто_админ"))
async def cmd_admins(message: types.Message):
    admins = await message.chat.get_administrators()
    admin_names = [f"• {a.user.full_name} (@{a.user.username})" if a.user.username else f"• {a.user.full_name}" for a in admins]

    text = "🛡 <b>Список администраторов чата:</b>\n\n" + "\n".join(admin_names)

    # Forward to Admin PMs if reply
    if message.reply_to_message:
        text += "\n\n📩 Сообщение созыва переслано администраторам!"

    await message.reply(text, parse_mode="HTML")

@router.message(F.text.lower().in_(["кто гарант", "созвать гарантов"]))
@router.message(Command("guarantors", "кто_гарант"))
async def cmd_guarantors(message: types.Message):
    await message.reply("⭐ <b>Гаранты чата:</b>\n\n• Назначенный гарант (@admin)\nИспользуйте `/profile` для отзывов.", parse_mode="HTML")

@router.message(F.text.lower().startswith("!повысить уровень"))
@router.message(F.text.lower().startswith("повысить уровень"))
@router.message(Command("level_up", "повысить_уровень"))
async def cmd_level_up(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(message.from_user.id)

        if user.level >= 5:
            await message.reply("🌟 У вас уже максимальный 5-й уровень!")
            return

        cost = LEVEL_COSTS.get(user.level, 1500.0)
        if user.rep_balance < cost:
            await message.reply(f"Недостаточно репутации! Повышение с {user.level} до {user.level + 1} уровня стоит {cost:.0f} Rep, у вас {user.rep_balance:.2f} Rep.")
            return

        await user_repo.deduct_rep(user.id, cost)
        user.level += 1
        await session.commit()

        await message.reply(f"🎉 Поздравляем! Ваш уровень повышен до <b>Участник [{user.level}]</b> (множитель +{user.level * 0.2:.1f}x)!", parse_mode="HTML")

@router.message(F.text.lower().startswith("топ недели"))
@router.message(Command("top_week"))
async def cmd_top_week(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        top = await user_repo.get_top_weekly_message_users(limit=15)

        text = "📊 <b>Топ-15 активных участников недели:</b>\n\n"
        for idx, (uid, msgs) in enumerate(top, start=1):
            text += f"<b>{idx}.</b> ID <code>{uid}</code> — {msgs} сообщений\n"

        await message.reply(text, parse_mode="HTML")

@router.message(F.text.lower().in_(["инструкция", "правила"]))
@router.message(Command("rules", "help_chat"))
async def cmd_chat_rules(message: types.Message):
    text = (
        "📜 <b>Правила и Инструкция чата:</b>\n\n"
        "1. Запрещен спам, рейд и оскорбления.\n"
        "2. Муты выдаются администраторами. Выкупить размут можно за репутацию под сообщением мута.\n"
        "3. Передать репутацию: `передать [сумма]` (комиссия 20%).\n"
        "4. Игры: `пощёчина`, `цуефа`, `кнб`.\n"
        "5. Оформить профиль и крутить титулы — в ЛС с ботом."
    )
    await message.reply(text, parse_mode="HTML")
