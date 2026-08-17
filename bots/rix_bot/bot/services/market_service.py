from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repositories.market_repo import MarketRepo
from bot.database.repositories.user_repo import UserRepo

class MarketService:
    @classmethod
    async def buy_title(
        cls,
        session: AsyncSession,
        buyer_id: int,
        listing_id: int
    ) -> Tuple[bool, str]:
        """
        Purchases title listing using pessimistic locking (FOR UPDATE) to prevent race conditions.
        Deducts 20% seller fee upon successful purchase.
        """
        market_repo = MarketRepo(session)
        user_repo = UserRepo(session)

        # Fetch listing with FOR UPDATE lock
        listing = await market_repo.get_listing_with_lock(listing_id)
        if not listing:
            return False, "Лот не найден или уже продан."

        if listing.seller_id == buyer_id:
            return False, "Вы не можете купить свой собственный лот."

        price = listing.price
        buyer = await user_repo.get_or_create(buyer_id)
        if buyer.rep_balance < price:
            return False, f"Недостаточно репутации! Цена: {price} Rep, у вас: {buyer.rep_balance} Rep."

        # Deduct from buyer
        await user_repo.deduct_rep(buyer_id, price)

        # Pay seller minus 20% fee
        seller_net = round(price * 0.8, 2)
        await user_repo.add_rep(listing.seller_id, seller_net)

        # Transfer title ownership
        await market_repo.add_user_title(buyer_id, listing.title_id)

        # Mark listing as inactive
        listing.is_active = False
        await session.flush()

        return True, f"Успешно куплено! Продавец получил {seller_net} Rep (комиссия 20%)."
