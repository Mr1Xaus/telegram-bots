from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from bot.database.session import AsyncSessionLocal
from bot.database.models.title import Title, UserTitle, TitleTypeEnum
from bot.services.title_service import TitleService

router = Router()

class MarketSellStates(StatesGroup):
    waiting_for_price = State()

def get_index_tab_keyboard(active_tab: str = "my") -> InlineKeyboardMarkup:
    my_btn_text = "🙋‍♂️ Мои титулы (Активно)" if active_tab == "my" else "🙋‍♂️ Мои титулы"
    all_btn_text = "🌐 Все титулы (Активно)" if active_tab == "all" else "🌐 Все титулы"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=my_btn_text, callback_data="title_tab:my"),
                InlineKeyboardButton(text=all_btn_text, callback_data="title_tab:all")
            ]
        ]
    )

@router.message(F.chat.type == "private", F.text.lower().in_(["📜 индекс титулов", "индекс титулов"]))
async def cmd_title_index(message: types.Message):
    await show_my_titles_tab(message)

@router.callback_query(F.data == "title_tab:my")
async def callback_tab_my(callback: types.CallbackQuery):
    await show_my_titles_tab(callback)

@router.callback_query(F.data == "title_tab:all")
async def callback_tab_all(callback: types.CallbackQuery):
    await show_all_titles_tab(callback)

async def show_my_titles_tab(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    async with AsyncSessionLocal() as session:
        await TitleService.seed_all_titles(session)
        stmt = (
            select(UserTitle, Title)
            .join(Title, UserTitle.title_id == Title.id)
            .where(UserTitle.user_id == user_id)
        )
        res = await session.execute(stmt)
        user_titles = list(res.all())

        tab_kb = get_index_tab_keyboard("my")
        keyboard_rows = tab_kb.inline_keyboard.copy()

        if not user_titles:
            text = "📜 <b>Индекс титулов — Мои титулы</b>\n\nУ вас пока нет ни одного титула. Испытайте удачу через `🎲 Крутить титул` (100 Rep)!"
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
            if isinstance(event, types.CallbackQuery):
                await event.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
            else:
                await event.answer(text, parse_mode="HTML", reply_markup=reply_markup)
            return

        text = f"🙋‍♂️ <b>Мои титулы ({len(user_titles)} шт):</b>\n\n"
        for ut, title in user_titles:
            eq_str = " (Надет)" if ut.is_equipped else ""
            text += f"• <b>{title.name}</b> x{ut.quantity}{eq_str}\n"
            
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"{'Снять' if ut.is_equipped else 'Носить'} {title.name}",
                    callback_data=f"title_equip:{title.id}"
                ),
                InlineKeyboardButton(
                    text=f"Продать {title.name}",
                    callback_data=f"title_sell:{title.id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await event.answer(text, parse_mode="HTML", reply_markup=reply_markup)

async def show_all_titles_tab(event: types.Message | types.CallbackQuery, page: int = 0):
    user_id = event.from_user.id
    async with AsyncSessionLocal() as session:
        await TitleService.seed_all_titles(session)
        stmt = select(Title).order_by(Title.type, Title.id)
        res = await session.execute(stmt)
        all_titles = list(res.scalars().all())

        tab_kb = get_index_tab_keyboard("all")
        keyboard_rows = tab_kb.inline_keyboard.copy()

        text = f"🌐 <b>Все титулы в системе ({len(all_titles)} шт):</b>\n<i>Нажмите на титул, чтобы узнать способ его получения:</i>\n\n"

        for title in all_titles:
            btn_text = f"{title.name} [{title.type.value}]"
            keyboard_rows.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"title_info:{title.id}")
            ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await event.answer(text, parse_mode="HTML", reply_markup=reply_markup)

@router.callback_query(F.data.startswith("title_info:"))
async def callback_title_info(callback: types.CallbackQuery):
    title_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(Title).where(Title.id == title_id)
        res = await session.execute(stmt)
        title = res.scalar_one()

        # Check ownership
        stmt_ut = select(UserTitle).where(UserTitle.user_id == user_id, UserTitle.title_id == title_id)
        res_ut = await session.execute(stmt_ut)
        ut = res_ut.scalar_one_or_none()

        ownership_str = f"В наличии: <b>{ut.quantity} шт</b>" if ut else "У вас пока нет этого титула."
        
        # Secret titles check
        if title.type == TitleTypeEnum.SECRET:
            obtain_method = "<b>???</b>"
        else:
            obtain_method = title.description or "Выпадает в рулетке или приобретается за выполнение ачивок."

        text = (
            f"👑 <b>Титул: {title.name}</b>\n"
            f"Категория: <b>{title.type.value}</b>\n"
            f"Статус: {ownership_str}\n\n"
            f"🎯 <b>Способ получения:</b>\n{obtain_method}"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад ко всем титулам", callback_data="title_tab:all")]
            ]
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("title_equip:"))
async def callback_equip_title(callback: types.CallbackQuery):
    title_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        stmt_all = select(UserTitle).where(UserTitle.user_id == user_id)
        res_all = await session.execute(stmt_all)
        for ut in res_all.scalars().all():
            if ut.title_id == title_id:
                ut.is_equipped = not ut.is_equipped
            else:
                ut.is_equipped = False
        await session.commit()

    await callback.answer("Статус титула обновлен!")
    await show_my_titles_tab(callback)

@router.callback_query(F.data.startswith("title_sell:"))
async def callback_sell_title(callback: types.CallbackQuery, state: FSMContext):
    title_id = int(callback.data.split(":")[1])
    await state.update_data(sell_title_id=title_id)
    await state.set_state(MarketSellStates.waiting_for_price)
    await callback.message.answer("🏷 <b>Введите цену продажи титула в Rep (число):</b>", parse_mode="HTML")
