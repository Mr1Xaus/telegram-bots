from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo
from bot.database.models.user import GenderEnum
from bot.utils.keyboards import get_gender_keyboard, get_main_pm_keyboard

router = Router()

@router.message(CommandStart())
@router.message(Command("start", "profile"))
async def cmd_profile(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(message.from_user.id)
        
        gender_str = {
            GenderEnum.MALE: "👨 Мужской",
            GenderEnum.FEMALE: "👩 Женский",
            GenderEnum.UNKNOWN: "❓ Не указан"
        }.get(user.gender, "❓ Не указан")

        text = (
            f"👤 <b>Профиль пользователя</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"🎭 Роль: <b>{user.role.value}</b>\n"
            f"⭐ Уровень: <b>{user.level}</b> (+{user.level * 0.2:.1f}x)\n"
            f"💰 Репутация: <b>{user.rep_balance:.2f} Rep</b>\n"
            f"⚧ Пол: <b>{gender_str}</b>\n"
            f"💍 Многоженство: <b>{'Да' if user.has_polygamy else 'Нет'}</b>\n"
            f"🔥 Квест-стрик: <b>{user.quest_streak} дней</b>\n"
        )
        
        reply_markup = get_main_pm_keyboard() if message.chat.type == "private" else (get_gender_keyboard() if user.gender == GenderEnum.UNKNOWN else None)
        await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)

@router.callback_query(F.data.startswith("set_gender:"))
async def callback_set_gender(callback: types.CallbackQuery):
    gender_code = callback.data.split(":")[1]
    gender_enum = GenderEnum(gender_code)
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(callback.from_user.id)
        user.gender = gender_enum
        await session.commit()
        
    await callback.answer("Пол успешно установлен!")
    await callback.message.edit_text(f"✅ Ваш пол успешно обновлен на: <b>{gender_enum.value}</b>", parse_mode="HTML")

@router.message(Command("buy_polygamy"))
async def cmd_buy_polygamy(message: types.Message):
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(message.from_user.id)
        
        if user.has_polygamy:
            await message.answer("У вас уже открыто многоженство!")
            return

        if user.rep_balance < 1000:
            await message.answer(f"Недостаточно репутации! Стоимость: 1000 Rep, у вас: {user.rep_balance:.2f} Rep.")
            return

        await user_repo.deduct_rep(user.id, 1000)
        user.has_polygamy = True
        await session.commit()
        
        await message.answer("🎉 Вы успешно приобрели услугу **Многоженство** (до 5 партнеров)!")
