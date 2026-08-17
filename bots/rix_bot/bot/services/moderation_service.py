from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.moderation import ModerationActionEnum
from bot.database.repositories.user_repo import UserRepo
from bot.database.repositories.moderation_repo import ModerationRepo

class ModerationService:
    @classmethod
    async def apply_mute_penalty(
        cls,
        session: AsyncSession,
        admin_id: int,
        target_id: int,
        chat_id: int,
        duration_seconds: int
    ) -> Tuple[float, int]:
        """
        Applies rep penalty for mute:
        <= 7h (25200s) -> -5 Rep
        > 7h -> -25 Rep
        Floor: Balance cannot drop below 0.
        """
        user_repo = UserRepo(session)
        mod_repo = ModerationRepo(session)

        penalty = 5.0 if duration_seconds <= 25200 else 25.0
        await user_repo.deduct_rep(target_id, penalty)

        await mod_repo.log_action(
            admin_id=admin_id,
            target_id=target_id,
            chat_id=chat_id,
            action=ModerationActionEnum.MUTE,
            duration_seconds=duration_seconds
        )

        unmute_cost = 50 if duration_seconds <= 25200 else 150
        return penalty, unmute_cost

    @classmethod
    async def buy_unmute(
        cls,
        session: AsyncSession,
        user_id: int,
        duration_seconds: int
    ) -> Tuple[bool, str]:
        """
        Buys unmute for rep:
        <= 7h: 50 reps
        > 7h: 150 reps
        """
        user_repo = UserRepo(session)
        unmute_cost = 50 if duration_seconds <= 25200 else 150

        user = await user_repo.get_or_create(user_id)
        if user.rep_balance < unmute_cost:
            return False, f"Недостаточно репутации для размута! Требуется: {unmute_cost} Rep, у вас: {user.rep_balance} Rep."

        await user_repo.deduct_rep(user_id, unmute_cost)
        return True, f"Мут успешно снят за {unmute_cost} Rep!"
