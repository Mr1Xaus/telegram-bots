import time
from typing import Tuple
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.user import GenderEnum
from bot.database.repositories.user_repo import UserRepo
from bot.database.repositories.marriage_repo import MarriageRepo

class MarriageService:
    COOLDOWNS = {
        "kiss": 3 * 3600,     # 3 hours
        "sleep": 5 * 3600,    # 5 hours
        "date": 3 * 3600,     # 3 hours
    }

    @classmethod
    async def propose_marriage(
        cls,
        session: AsyncSession,
        user_id: int,
        partner_id: int
    ) -> Tuple[bool, str]:
        user_repo = UserRepo(session)
        marriage_repo = MarriageRepo(session)

        u1 = await user_repo.get_or_create(user_id)
        u2 = await user_repo.get_or_create(partner_id)

        if u1.gender == GenderEnum.UNKNOWN or u2.gender == GenderEnum.UNKNOWN:
            return False, "Для вступления в брак оба пользователя должны указать пол в профиле (`/profile`)!"

        if await marriage_repo.is_married(user_id, partner_id):
            return False, "Вы уже состоите в браке с этим пользователем!"

        # Check partner limit for u1
        u1_count = await marriage_repo.get_partner_count(user_id)
        max_u1 = 5 if u1.has_polygamy else 1
        if u1_count >= max_u1:
            return False, f"Вы достигли лимита браков ({u1_count}/{max_u1}). Для расширения откройте многоженство!"

        # Check partner limit for u2
        u2_count = await marriage_repo.get_partner_count(partner_id)
        max_u2 = 5 if u2.has_polygamy else 1
        if u2_count >= max_u2:
            return False, f"Ваш партнер достиг лимита браков ({u2_count}/{max_u2})!"

        await marriage_repo.create_marriage(user_id, partner_id)
        return True, "💍 Поздравляем! Вы официально вступили в брак!"

    @classmethod
    async def interact(
        cls,
        redis: Redis,
        action: str,
        user_id: int,
        partner_id: int
    ) -> Tuple[bool, str]:
        cd_seconds = cls.COOLDOWNS.get(action, 3600)
        key = f"marriage_interaction:{action}:{user_id}:{partner_id}"
        
        if redis is not None:
            ttl = await redis.ttl(key)
            if ttl > 0:
                hours = ttl // 3600
                minutes = (ttl % 3600) // 60
                return False, f"⏳ Кулдаун еще не прошел! Попробуйте через {hours} ч {minutes} мин."

            await redis.setex(key, cd_seconds, int(time.time()))
        
        messages = {
            "kiss": "😘 Вы страстно поцеловали своего партнера!",
            "sleep": "🔥 Вы провели незабываемую ночь вместе!",
            "date": "🍷 Вы сходили на романтическое свидание!",
        }
        return True, messages.get(action, "Взаимодействие выполнено!")
