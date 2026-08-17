from typing import List, Optional
from sqlalchemy import select, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.marriage import Marriage

class MarriageRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_marriages(self, user_id: int) -> List[Marriage]:
        stmt = select(Marriage).where(or_(Marriage.user_id == user_id, Marriage.partner_id == user_id))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_partner_count(self, user_id: int) -> int:
        marriages = await self.get_marriages(user_id)
        return len(marriages)

    async def is_married(self, u1: int, u2: int) -> bool:
        stmt = select(Marriage).where(
            or_(
                and_(Marriage.user_id == u1, Marriage.partner_id == u2),
                and_(Marriage.user_id == u2, Marriage.partner_id == u1),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_marriage(self, u1: int, u2: int) -> Marriage:
        min_id, max_id = min(u1, u2), max(u1, u2)
        marriage = Marriage(user_id=min_id, partner_id=max_id)
        self.session.add(marriage)
        await self.session.flush()
        return marriage

    async def divorce(self, u1: int, u2: int) -> bool:
        stmt = delete(Marriage).where(
            or_(
                and_(Marriage.user_id == u1, Marriage.partner_id == u2),
                and_(Marriage.user_id == u2, Marriage.partner_id == u1),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
