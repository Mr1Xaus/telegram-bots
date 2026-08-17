from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.moderation import ModerationLog, ModerationActionEnum

class ModerationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        admin_id: int,
        target_id: int,
        chat_id: int,
        action: ModerationActionEnum,
        duration_seconds: Optional[int] = None
    ) -> ModerationLog:
        log = ModerationLog(
            admin_id=admin_id,
            target_id=target_id,
            chat_id=chat_id,
            action=action,
            duration_seconds=duration_seconds
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_weekly_admin_mutes(self, start_of_week: datetime) -> List[Tuple[int, int]]:
        stmt = (
            select(ModerationLog.admin_id, func.count(ModerationLog.id).label("mute_count"))
            .where(
                ModerationLog.action == ModerationActionEnum.MUTE,
                ModerationLog.created_at >= start_of_week
            )
            .group_by(ModerationLog.admin_id)
            .order_by(func.count(ModerationLog.id).desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]
