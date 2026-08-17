from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.user import User, ChatStats, UserRoleEnum, GenderEnum

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_id)
            self.session.add(user)
            await self.session.flush()
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_active(self, user_id: int):
        stmt = update(User).where(User.id == user_id).values(last_active_at=datetime.now(timezone.utc))
        await self.session.execute(stmt)

    async def get_chat_stats(self, user_id: int, chat_id: int) -> ChatStats:
        stmt = select(ChatStats).where(ChatStats.user_id == user_id, ChatStats.chat_id == chat_id)
        result = await self.session.execute(stmt)
        stats = result.scalar_one_or_none()
        if not stats:
            stats = ChatStats(user_id=user_id, chat_id=chat_id)
            self.session.add(stats)
            await self.session.flush()
        return stats

    async def increment_message_count(self, user_id: int, chat_id: int) -> Tuple[int, ChatStats]:
        stats = await self.get_chat_stats(user_id, chat_id)
        stats.msg_count_week += 1
        stats.msg_count_month += 1
        stats.msg_count_total += 1
        await self.session.flush()
        return stats.msg_count_total, stats

    async def add_rep(self, user_id: int, amount: float):
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.rep_balance = max(0.0, user.rep_balance + amount)
            await self.session.flush()

    async def deduct_rep(self, user_id: int, amount: float) -> bool:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.rep_balance >= amount:
            user.rep_balance -= amount
            await self.session.flush()
            return True
        return False

    async def get_top_weekly_message_users(self, limit: int = 7) -> List[Tuple[int, int]]:
        stmt = (
            select(ChatStats.user_id, func.sum(ChatStats.msg_count_week).label("total_msgs"))
            .group_by(ChatStats.user_id)
            .order_by(func.sum(ChatStats.msg_count_week).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def reset_weekly_counters(self):
        await self.session.execute(update(ChatStats).values(msg_count_week=0, rep_earned_week=0.0))
