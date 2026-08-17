from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo
from bot.database.models.user import GenderEnum
from bot.services.title_service import TitleService
from bot.services.quest_service import QuestService
from bot.utils.keyboards import (
    get_main_pm_keyboard,
    get_profile_customization_keyboard,
    get_gender_keyboard
)

router = Router()

@router.message(F.chat.type == "private", F.text == "👤 Профиль")
async def btn_profile(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(message.from_user.id)
        
        gender_str = {
            GenderEnum.MALE: "👨 Мужской",
            GenderEnum.FEMALE: "👩 Женский",
            GenderEnum.UNKNOWN: "❓ Не указан"
        }.get(user.gender, "❓ Не указан")

        guarantor_str = ""
        if user.is_guarantor:
            guarantor_str = f"\n⭐ Статус: <b>Гарант</b>\n🔗 Отзывы: {user.guarantor_reviews_url or 'Не указаны'}\n🛡 Ручения: <b>{user.guarantor_guarantees_sum:.2f} Rep</b>"

        text = (
            f"👤 <b>Профиль пользователя</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"🎭 Роль: <b>{user.role.value}</b>{guarantor_str}\n"
            f"⭐ Уровень: <b>{user.level}</b> (+{user.level * 0.2:.1f}x)\n"
            f"💰 Репутация: <b>{user.rep_balance:.2f} Rep</b>\n"
            f"⚧ Пол: <b>{gender_str}</b>\n"
            f"💍 Многоженство: <b>{'Да' if user.has_polygamy else 'Нет'}</b>\n"
            f"🔥 Квест-стрик: <b>{user.quest_streak} дней</b>\n"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_pm_keyboard())

@router.message(F.chat.type == "private", F.text == "⚙️ Оформить профиль")
async def btn_customize(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(message.from_user.id)
        kb = get_profile_customization_keyboard(user.is_guarantor)
        await message.answer("⚙️ <b>Меню оформления профиля:</b>", parse_mode="HTML", reply_markup=kb)

@router.message(F.chat.type == "private", F.text == "📖 Инструкция")
async def btn_instruction(message: types.Message):
    text = (
        "📖 <b>Инструкция пользования ботом RiX</b>\n\n"
        "1. <b>Экономика:</b> Каждые 100 сообщений в чатах наносят +1 Rep. Репутацию можно передавать командой `передать 50`.\n"
        "2. <b>Профиль и Пол:</b> Выберите пол в ЛС (`⚙️ Оформить профиль`). Без выбора пола в брак вступить нельзя!\n"
        "3. <b>Браки:</b> Обычный брак — 1 партнер. `buy_polygamy` (1000 Rep) расширяет гарем до 5 партнеров.\n"
        "4. <b>Титулы и Маркет:</b> Крутите титулы (100 Rep) или покупайте/продавайте их на маркете (`🛒 Маркет титулов`).\n"
        "5. <b>Квесты:</b> Выполняйте ежедневные задания (`🎯 Мои квесты`), чтобы повышать свой квест-стрик!"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_pm_keyboard())

@router.message(F.chat.type == "private", F.text == "🛒 Маркет титулов")
async def btn_market(message: types.Message):
    from bot.handlers.private.market import show_market_page
    await show_market_page(message, page=0)

@router.message(F.chat.type == "private", F.text == "🎲 Крутить титул (100 Rep)")
async def btn_spin_title(message: types.Message):
    async with AsyncSessionLocal() as session:
        success, msg = await TitleService.spin_rng_title(session, message.from_user.id)
        if success:
            await session.commit()
            await message.answer(f"🎉 {msg}", parse_mode="HTML")
        else:
            await message.answer(f"❌ {msg}")

@router.message(F.chat.type == "private", F.text == "🎯 Мои квесты")
async def btn_quests(message: types.Message):
    async with AsyncSessionLocal() as session:
        quests = await QuestService.get_user_quests(session, message.from_user.id)
        
        text = "🎯 <b>Ваши ежедневные квесты:</b>\n\n"
        desc_map = {item[0]: item[1] for item in QuestService.DAILY_QUESTS}
        for q in quests:
            status = "✅" if q.is_completed else f"[{q.progress}/{q.target}]"
            desc = desc_map.get(q.quest_key, q.quest_key)
            text += f"• {desc}: <b>{status}</b> (+2.0 Rep)\n"
            
        await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("cust:"))
async def callback_customization(callback: types.CallbackQuery):
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    if action == "select_gender":
        await callback.message.edit_text("Выберите ваш пол:", reply_markup=get_gender_keyboard())
    elif action == "change_gender":
        async with AsyncSessionLocal() as session:
            user_repo = UserRepo(session)
            success = await user_repo.deduct_rep(user_id, 100.0)
            if success:
                await session.commit()
                await callback.message.edit_text("Пол сброшен (списано 100 Rep). Выберите новый пол:", reply_markup=get_gender_keyboard())
            else:
                await callback.answer("Недостаточно репутации! Смена пола стоит 100 Rep.", show_alert=True)
    elif action == "avatar":
        await callback.answer("Функция кастомной аватарки отправлена модератору на рассмотрение (150 Rep).", show_alert=True)
