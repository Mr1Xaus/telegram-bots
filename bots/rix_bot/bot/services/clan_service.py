from typing import Tuple, List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.clan import Clan, ClanMember
from bot.database.repositories.user_repo import UserRepo

class ClanService:
    @classmethod
    async def create_clan(cls, session: AsyncSession, owner_id: int, name: str) -> Tuple[bool, str]:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(owner_id)

        # Check if already in a clan
        stmt_m = select(ClanMember).where(ClanMember.user_id == owner_id)
        res_m = await session.execute(stmt_m)
        if res_m.scalar_one_or_none():
            return False, "Вы уже состоите в клане! Сначала покиньте или расформируйте его."

        if user.rep_balance < 1500.0:
            return False, f"Недостаточно репутации для создания клана! Требуется: 1500 Rep, у вас: {user.rep_balance:.2f} Rep."

        # Check unique name
        stmt_c = select(Clan).where(Clan.name == name)
        res_c = await session.execute(stmt_c)
        if res_c.scalar_one_or_none():
            return False, "Клан с таким названием уже существует!"

        await user_repo.deduct_rep(owner_id, 1500.0)
        clan = Clan(name=name, owner_id=owner_id, max_slots=5)
        session.add(clan)
        await session.flush()

        member = ClanMember(user_id=owner_id, clan_id=clan.id)
        session.add(member)
        await session.flush()

        return True, f"🏰 Клан <b>{name}</b> успешно создан!"

    @classmethod
    async def disband_clan(cls, session: AsyncSession, user_id: int) -> Tuple[bool, str]:
        stmt = select(Clan).where(Clan.owner_id == user_id)
        res = await session.execute(stmt)
        clan = res.scalar_one_or_none()
        if not clan:
            return False, "Вы не являетесь владельцем клана!"

        # Delete members
        stmt_del = delete(ClanMember).where(ClanMember.clan_id == clan.id)
        await session.execute(stmt_del)
        await session.delete(clan)
        await session.flush()

        return True, f"🏰 Клан <b>{clan.name}</b> расформирован."
