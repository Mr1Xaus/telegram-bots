from typing import Optional, List, Tuple
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.title import Title, UserTitle, MarketListing

class MarketRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_listings(self, limit: int = 10, offset: int = 0) -> List[Tuple[MarketListing, Title]]:
        stmt = (
            select(MarketListing, Title)
            .join(Title, MarketListing.title_id == Title.id)
            .where(MarketListing.is_active == True)
            .order_by(MarketListing.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_listing_with_lock(self, listing_id: int) -> Optional[MarketListing]:
        """
        Pessimistic lock FOR UPDATE for strict concurrency safety
        """
        stmt = (
            select(MarketListing)
            .where(MarketListing.id == listing_id, MarketListing.is_active == True)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_listing(self, seller_id: int, title_id: int, price: int) -> MarketListing:
        listing = MarketListing(seller_id=seller_id, title_id=title_id, price=price, is_active=True)
        self.session.add(listing)
        await self.session.flush()
        return listing

    async def add_user_title(self, user_id: int, title_id: int):
        stmt = select(UserTitle).where(UserTitle.user_id == user_id, UserTitle.title_id == title_id)
        result = await self.session.execute(stmt)
        user_title = result.scalar_one_or_none()
        if user_title:
            user_title.quantity += 1
        else:
            user_title = UserTitle(user_id=user_id, title_id=title_id, quantity=1, is_equipped=False)
            self.session.add(user_title)
        await self.session.flush()

    async def remove_user_title(self, user_id: int, title_id: int) -> bool:
        stmt = select(UserTitle).where(UserTitle.user_id == user_id, UserTitle.title_id == title_id)
        result = await self.session.execute(stmt)
        user_title = result.scalar_one_or_none()
        if not user_title or user_title.quantity <= 0:
            return False
        user_title.quantity -= 1
        if user_title.quantity == 0:
            await self.session.delete(user_title)
        await self.session.flush()
        return True
