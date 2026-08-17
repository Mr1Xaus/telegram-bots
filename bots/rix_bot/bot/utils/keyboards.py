from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_unmute_keyboard(target_id: int, duration_seconds: int) -> InlineKeyboardMarkup:
    cost = 50 if duration_seconds <= 25200 else 150
    btn = InlineKeyboardButton(
        text=f"🔓 Выкупить размут ({cost} Rep)",
        callback_data=f"buy_unmute:{target_id}:{duration_seconds}"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])

def get_gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужской", callback_data="set_gender:MALE"),
                InlineKeyboardButton(text="👩 Женский", callback_data="set_gender:FEMALE")
            ]
        ]
    )

def get_marriage_proposal_keyboard(proposer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"marriage_accept:{proposer_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"marriage_reject:{proposer_id}")
            ]
        ]
    )

def get_market_slider_keyboard(listing_id: int, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"market_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"market_page:{page + 1}"))
    
    buy_btn = InlineKeyboardButton(text="🛒 Купить титул", callback_data=f"buy_title:{listing_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[buy_btn], nav])
