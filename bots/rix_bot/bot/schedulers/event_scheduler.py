import logging
import random
from aiogram import Bot
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo

async def run_hourly_active_randomizer(bot: Bot):
    """
    Hourly randomizer picker for active chatters (+10 reps)
    """
    logging.info("Running hourly active chatter randomizer...")
    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        top_users = await user_repo.get_top_weekly_message_users(limit=20)
        if top_users:
            winner_id, _ = random.choice(top_users)
            await user_repo.add_rep(winner_id, 10.0)
            await session.commit()
            logging.info(f"Awarded 10 Rep to active user {winner_id}")
