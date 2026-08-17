from typing import Tuple, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.quest import Quest, QuestTypeEnum
from bot.database.repositories.user_repo import UserRepo

class QuestService:
    DAILY_QUESTS = [
        ("msg_150", "Отправить 150 сообщений", 150, 2.0),
        ("all_chats", "Отправить по сообщению во всех чатах", 1, 2.0),
        ("mod_action", "Вызвать админов или выдача мута", 1, 2.0),
        ("win_rps", "Победить 1 раз в Цуефа", 1, 2.0),
    ]

    @classmethod
    async def get_user_quests(cls, session: AsyncSession, user_id: int) -> List[Quest]:
        stmt = select(Quest).where(Quest.user_id == user_id, Quest.quest_type == QuestTypeEnum.DAILY)
        res = await session.execute(stmt)
        quests = list(res.scalars().all())

        if not quests:
            # Seed daily quests
            for key, desc, target, reward in cls.DAILY_QUESTS:
                q = Quest(user_id=user_id, quest_key=key, target=target, quest_type=QuestTypeEnum.DAILY)
                session.add(q)
                quests.append(q)
            await session.flush()
        return quests

    @classmethod
    async def update_quest_progress(cls, session: AsyncSession, user_id: int, quest_key: str, amount: int = 1):
        quests = await cls.get_user_quests(session, user_id)
        user_repo = UserRepo(session)
        
        for q in quests:
            if q.quest_key == quest_key and not q.is_completed:
                q.progress += amount
                if q.progress >= q.target:
                    q.is_completed = True
                    q.completed_at = datetime.now(timezone.utc)
                    # Reward +2 rep
                    await user_repo.add_rep(user_id, 2.0)
                await session.flush()

    @classmethod
    async def restore_streak(cls, session: AsyncSession, user_id: int) -> Tuple[bool, str]:
        user_repo = UserRepo(session)
        user = await user_repo.get_or_create(user_id)

        if not user.streak_broken_at:
            return False, "У вас нет прерванной серии квестов для восстановления!"

        now = datetime.now(timezone.utc)
        if now > user.streak_broken_at + timedelta(days=3):
            return False, "3-дневное окно восстановления серии истекло!"

        if user.rep_balance < 300.0:
            return False, f"Недостаточно репутации для восстановления серии! Требуется 300 Rep, у вас {user.rep_balance:.2f} Rep."

        await user_repo.deduct_rep(user_id, 300.0)
        user.streak_broken_at = None
        await session.flush()
        return True, f"🔥 Серия квестов ({user.quest_streak} дней) успешно восстановлена!"
