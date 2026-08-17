from typing import Tuple
from bot.database.models.user import User, UserRoleEnum
from bot.database.repositories.user_repo import UserRepo

class EconomyService:
    LEVEL_BONUSES = {
        0: 0.0,
        1: 0.2,
        2: 0.4,
        3: 0.6,
        4: 0.8,
        5: 1.0,
    }

    @classmethod
    def calculate_multiplier(
        cls,
        user: User,
        is_event_active: bool = False
    ) -> float:
        """
        Calculates total additive multiplier:
        Total Multiplier = 1.0 + LevelBonus + RankBonus + TitleBonus + EventBonus
        """
        multiplier = 1.0
        
        # Level bonus
        multiplier += cls.LEVEL_BONUSES.get(user.level, 0.0)
        
        # Rank bonus
        if user.role == UserRoleEnum.ADMIN_A:
            multiplier += 0.2
            
        # Title All-in-One bonus
        if user.has_all_in_one:
            multiplier += 0.5
            
        # Active Event bonus
        if is_event_active:
            multiplier += 0.2
            
        return round(multiplier, 2)

    @classmethod
    async def process_message_reward(
        cls,
        user_repo: UserRepo,
        user_id: int,
        chat_id: int,
        is_event_active: bool = False
    ) -> Tuple[bool, float]:
        """
        Grants rep every 100 messages (+1 rep base) and extra milestone (+5 rep) at 500 msgs.
        """
        user = await user_repo.get_or_create(user_id)
        total_msgs, stats = await user_repo.increment_message_count(user_id, chat_id)
        
        base_rep = 0.0
        
        # Every 100 messages milestone
        if total_msgs % 100 == 0:
            base_rep += 1.0
            
        # Every 500 messages milestone
        if total_msgs % 500 == 0:
            base_rep += 5.0
            
        if base_rep > 0:
            multiplier = cls.calculate_multiplier(user, is_event_active)
            earned_rep = base_rep * multiplier
            await user_repo.add_rep(user_id, earned_rep)
            return True, earned_rep
            
        return False, 0.0

    @classmethod
    async def transfer_rep(
        cls,
        user_repo: UserRepo,
        sender_id: int,
        receiver_id: int,
        amount: float
    ) -> Tuple[bool, str, float]:
        """
        Transfers rep with 20% commission deducted. Multipliers do NOT apply.
        """
        if amount <= 0:
            return False, "Сумма передачи должна быть больше 0.", 0.0

        if sender_id == receiver_id:
            return False, "Нельзя переводить репутацию самому себе.", 0.0

        success = await user_repo.deduct_rep(sender_id, amount)
        if not success:
            return False, "Недостаточно репутации на балансе.", 0.0

        net_amount = round(amount * 0.8, 2)  # 20% fee
        await user_repo.add_rep(receiver_id, net_amount)
        await user_repo.get_or_create(receiver_id)

        return True, f"Успешный перевод! Списано комиссией 20%. Получено: {net_amount} Rep.", net_amount
