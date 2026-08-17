import random
from typing import Tuple, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.title import Title, UserTitle, TitleTypeEnum
from bot.database.repositories.user_repo import UserRepo

RNG_TITLES_LIST = [
    "Клоун", "Фанатик", "RNG Жертва", "Нуб", "Неудачник",
    "Пациент", "Фортуна", "{#@!:™##}", "RIP", "Бедолага",
    "Бог неудач", "Смертник", "Коммунист", "Гоблин", "Косой",
    "Верующий", "Везунчик", "Инвалид", "Фощист", "Психопат",
    "Полицай", "Анонимус", "Курящий", "Сигма", "Хомелион"
]

class TitleService:
    @classmethod
    async def seed_rng_titles(cls, session: AsyncSession):
        for name in RNG_TITLES_LIST:
            stmt = select(Title).where(Title.name == name)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                t = Title(name=name, type=TitleTypeEnum.RNG, description=f"RNG Титул '{name}'")
                session.add(t)
        await session.flush()

    @classmethod
    async def spin_rng_title(cls, session: AsyncSession, user_id: int) -> Tuple[bool, str]:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(user_id)

        if user.rep_balance < 100.0:
            return False, f"Недостаточно репутации для прокрута! Стоимость: 100 Rep, у вас: {user.rep_balance:.2f} Rep."

        await cls.seed_rng_titles(session)
        await user_repo.deduct_rep(user_id, 100.0)

        title_name = random.choice(RNG_TITLES_LIST)
        stmt = select(Title).where(Title.name == title_name)
        res = await session.execute(stmt)
        title = res.scalar_one()

        # Add to user titles
        stmt_ut = select(UserTitle).where(UserTitle.user_id == user_id, UserTitle.title_id == title.id)
        res_ut = await session.execute(stmt_ut)
        ut = res_ut.scalar_one_or_none()
        if ut:
            ut.quantity += 1
        else:
            ut = UserTitle(user_id=user_id, title_id=title.id, quantity=1, is_equipped=False)
            session.add(ut)

        await session.flush()
        return True, f"🎲 Вам выпал титул: <b>{title_name}</b>!"
