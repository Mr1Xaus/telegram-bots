from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from bot.database.session import AsyncSessionLocal
from bot.database.models.title import Title, UserTitle, MarketListing
from bot.database.repositories.user_repo import UserRepo

router = Router()

class MarketSellStates(StatesGroup):
    waiting_for_price = State()

@router.message(F.chat.type == "private", F.text.lower().in_(["📜 индекс титулов", "индекс титулов"]))
async def cmd_title_index(message: types.Message):
    await show_title_index(message)

async def show_title_index(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    async with AsyncSessionLocal() as session:
        stmt = (
            select(UserTitle, Title)
            .join(Title, UserTitle.title_id == Title.id)
            .where(UserTitle.user_id == user_id)
        )
        res = await session.execute(stmt)
        user_titles = list(res.all())

        if not user_titles:
            text = "📜 <b>Индекс титулов</b>\n\nУ вас пока нет ни одного титула. Испытайте удачу через `🎲 Крутить титул` (100 Rep)!"
            if isinstance(event, types.CallbackQuery):
                await event.answer("У вас нет титулов.")
            else:
                await event.answer(text, parse_mode="HTML")
            return

        text = f"📜 <b>Индекс ваших титулов ({len(user_titles)} шт):</b>\n\n"
        keyboard_rows = []

        for ut, title in user_titles:
            eq_str = " (Надет)" if ut.is_equipped else ""
            text += f"• <b>{title.name}</b> x{ut.quantity}{eq_str}\n"
            
            row = [
                InlineKeyboardButton(
                    text=f"{'Снять' if ut.is_equipped else 'Носить'} {title.name}",
                    callback_data=f"title_equip:{title.id}"
                ),
                InlineKeyboardButton(
                    text=f"Sell {title.name}",
                    callback_data=f"title_sell:{title.id}"
                )
            ]
            keyboard_rows.append(row)

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await event.answer(text, parse_mode="HTML", reply_markup=reply_markup)

@router.callback_query(F.data.startswith("title_equip:"))
async def callback_equip_title(callback: types.CallbackQuery):
    title_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        # Unequip all titles first
        stmt_all = select(UserTitle).where(UserTitle.user_id == user_id)
        res_all = await session.execute(stmt_all)
        for ut in res_all.scalars().all():
            if ut.title_id == title_id:
                ut.is_equipped = not ut.is_equipped
            else:
                ut.is_equipped = False
        await session.commit()

    await callback.answer("Статус титула обновлен!")
    await show_title_index(callback)

@router.callback_query(F.data.startswith("title_sell:"))
async def callback_sell_title(callback: types.CallbackQuery, state: FSMContext):
    title_id = int(callback.data.split(":")[1])
    await state.update_data(sell_title_id=title_id)
    await state.set_state(MarketSellStates.waiting_for_price)
    await callback.message.answer("🏷 <b>Введите цену продажи титула в Rep (число):</b>", parse_mode="HTML")

@router.message(MarketSellStates.waiting_for_price)
async def process_sell_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title_id = data.get("sell_title_id")
    
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError()
    except Exception:
        await message.answer("Пожалуйста, введите положительное целое число для цены.")
        return

    async with AsyncSessionLocal() as session:
        # Remove 1 quantity from user
        stmt = select(UserTitle).where(UserTitle.user_id == message.from_user.id, UserTitle.title_id == title_id)
        res = await session.execute(stmt)
        ut = res.scalar_one_or_none()
        
        if not ut or ut.quantity <= 0:
            await message.answer("Ошибка: у вас больше нет этого титула.")
            await state.clear()
            return

        ut.quantity -= 1
        if ut.quantity == 0:
            await session.delete(ut)

        # Create market listing
        listing = MarketListing(seller_id=message.from_user.id, title_id=title_id, price=price, is_active=True)
        session.add(listing)
        await session.commit()

    await state.clear()
    await message.answer(f"✅ Титул успешно выставлен на маркет за <b>{price} Rep</b> (комиссия 20% при покупке).", parse_mode="HTML")
