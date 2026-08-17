from typing import Optional, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.clan import Clan, ClanMember

class ClanRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_clan(self, name: str, owner_id: int) -> Clan:
        clan = Clan(name=name, owner_id=owner_id)
        self.session.add(clan)
        await self.session.flush()
        # Auto-add owner as member
        member = ClanMember(user_id=owner_id, clan_id=clan.id)
        self.session.add(member)
        await self.session.flush()
        return clan

    async def get_by_id(self, clan_id: int) -> Optional[Clan]:
        stmt = select(Clan).where(Clan.id == clan_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_clan(self, user_id: int) -> Optional[Clan]:
        stmt = select(Clan).join(ClanMember, Clan.id == ClanMember.clan_id).where(ClanMember.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_member_count(self, clan_id: int) -> int:
        stmt = select(func.count(ClanMember.user_id)).where(ClanMember.clan_id == clan_id)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def add_member(self, user_id: int, clan_id: int) -> bool:
        clan = await self.get_by_id(clan_id)
        if not clan:
            return False
        count = await self.get_member_count(clan_id)
        if count >= clan.max_slots:
            return False
        member = ClanMember(user_id=user_id, clan_id=clan_id)
        self.session.add(member)
        await self.session.flush()
        return True

    async def remove_member(self, user_id: int):
        stmt = delete(ClanMember).where(ClanMember.user_id == user_id)
        await self.session.execute(stmt)
