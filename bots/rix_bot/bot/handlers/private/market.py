from aiogram import Router, F, types
from aiogram.filters import Command
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.market_repo import MarketRepo
from bot.services.market_service import MarketService
from bot.utils.keyboards import get_market_slider_keyboard

router = Router()

@router.message(Command("market"))
async def cmd_market(message: types.Message):
    await show_market_page(message, page=0)

async def show_market_page(event: types.Message | types.CallbackQuery, page: int = 0):
    async with AsyncSessionLocal() as session:
        market_repo = MarketRepo(session)
        listings = await market_repo.get_active_listings(limit=1, offset=page)
        
        if not listings:
            text = "🛒 **Магазин титулов пуст.**"
            if isinstance(event, types.CallbackQuery):
                await event.answer("Больше нет лотов.")
            else:
                await event.answer(text)
            return

        listing, title = listings[0]
        total_pages = 10  # simplified max pages

        text = (
            f"🏷 <b>Лот #{listing.id}</b>\n\n"
            f"👑 Титул: <b>{title.name}</b> ({title.type.value})\n"
            f"📝 Описание: {title.description or 'Отсутствует'}\n"
            f"💰 Цена: <b>{listing.price} Rep</b>\n"
            f"👤 Продавец ID: <code>{listing.seller_id}</code>\n"
        )
        
        reply_markup = get_market_slider_keyboard(listing.id, page, total_pages)
        
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await event.answer(text, parse_mode="HTML", reply_markup=reply_markup)

@router.callback_query(F.data.startswith("market_page:"))
async def callback_market_page(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    await show_market_page(callback, page=page)

@router.callback_query(F.data.startswith("buy_title:"))
async def callback_buy_title(callback: types.CallbackQuery):
    listing_id = int(callback.data.split(":")[1])
    buyer_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        success, msg = await MarketService.buy_title(session, buyer_id, listing_id)
        if success:
            await session.commit()
            await callback.answer("Покупка успешно совершена!", show_alert=True)
            await callback.message.edit_text(f"✅ {msg}")
        else:
            await callback.answer(msg, show_alert=True)
