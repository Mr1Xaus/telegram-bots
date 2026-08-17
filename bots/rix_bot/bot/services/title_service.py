import random
from typing import Tuple, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.title import Title, UserTitle, TitleTypeEnum
from bot.database.repositories.user_repo import UserRepo

ALL_SYSTEM_TITLES = [
    # RNG Titles (25)
    ("Клоун", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Фанатик", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("RNG Жертва", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Нуб", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Неудачник", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Пациент", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Фортуна", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("{#@!:™##}", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("RIP", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Бедолага", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Бог неудач", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Смертник", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Коммунист", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Гоблин", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Косой", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Верующий", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Везунчик", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Инвалид", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Фощист", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Психопат", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Полицай", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Анонимус", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Курящий", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Сигма", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    ("Хомелион", TitleTypeEnum.RNG, "Выпадает случайно через рулетку (100 Rep)."),
    
    # Achievement Titles (10)
    ("All-in For-One..", TitleTypeEnum.ACHIEVEMENT, "Дается ВЗАМЕН абсолютно всех титулов (кроме секретных). Бонус: +0.5 к репе."),
    ("MarketVictim💸", TitleTypeEnum.ACHIEVEMENT, "Купить за 500 Rep при условии 10+ покупок на 1500+ Rep за одну неделю."),
    ("Rep farmer💰", TitleTypeEnum.ACHIEVEMENT, "Купить за 300 Rep при условии полного выполнения 30 ежедневных квестов подряд."),
    ("WifeCollector🫀", TitleTypeEnum.ACHIEVEMENT, "Купить за 300 Rep при условии сбора полного гарема в браке."),
    ("Title chaser🧩", TitleTypeEnum.ACHIEVEMENT, "Купить за 150 Rep при условии сбора всей коллекции RNG титулов."),
    ("Clan Master⚔️", TitleTypeEnum.ACHIEVEMENT, "Купить за 300 Rep при условии занятия 1 места кланом за месяц."),
    ("He has no life🫂", TitleTypeEnum.ACHIEVEMENT, "Купить за 300 Rep при условии написания 3000 сообщений за день."),
    ("Smartass🔮", TitleTypeEnum.ACHIEVEMENT, "Купить за 500 Rep при условии первенства в 5 задачах ивента подряд."),
    ("Big dealer🌐", TitleTypeEnum.ACHIEVEMENT, "Купить за 500 Rep при условии перевода 1000+ Rep за один раз."),
    ("Discipline🛡", TitleTypeEnum.ACHIEVEMENT, "Купить за 300 Rep при условии серии из 50 ежедневных квестов."),

    # Secret Titles (3) -> "???"
    ("⚜️A true hero", TitleTypeEnum.SECRET, "???"),
    ("⚜️Costume drama", TitleTypeEnum.SECRET, "???"),
    ("⚜️Sinking together", TitleTypeEnum.SECRET, "???"),
]

RNG_TITLES_LIST = [t[0] for t in ALL_SYSTEM_TITLES if t[1] == TitleTypeEnum.RNG]

class TitleService:
    @classmethod
    async def seed_all_titles(cls, session: AsyncSession):
        for name, t_type, desc in ALL_SYSTEM_TITLES:
            stmt = select(Title).where(Title.name == name)
            res = await session.execute(stmt)
            t = res.scalar_one_or_none()
            if not t:
                t = Title(name=name, type=t_type, description=desc)
                session.add(t)
            else:
                t.type = t_type
                t.description = desc
        await session.flush()

    @classmethod
    async def spin_rng_title(cls, session: AsyncSession, user_id: int) -> Tuple[bool, str]:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(user_id)

        if user.rep_balance < 100.0:
            return False, f"Недостаточно репутации для прокрута! Стоимость: 100 Rep, у вас: {user.rep_balance:.2f} Rep."

        await cls.seed_all_titles(session)
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
