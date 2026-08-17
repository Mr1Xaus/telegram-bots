import logging
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from sqlalchemy import select, update
from bot.database.session import AsyncSessionLocal
from bot.database.models.user import User, UserRoleEnum
from bot.database.repositories.user_repo import UserRepo
from bot.database.repositories.moderation_repo import ModerationRepo

async def run_weekly_reset(bot: Bot):
    logging.info("Starting Weekly Reset job...")
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepo(session)
        mod_repo = ModerationRepo(session)

        # 1. Recalculate A-Rank admins (Top 5 highest mute count)
        top_mutes = await mod_repo.get_weekly_admin_mutes(start_of_week)
        top_5_admin_ids = [admin_id for admin_id, count in top_mutes[:5]]

        # Set top 5 to ADMIN_A, other admins to ADMIN_B
        all_admins_stmt = select(User).where(User.role.in_([UserRoleEnum.ADMIN_A, UserRoleEnum.ADMIN_B]))
        res = await session.execute(all_admins_stmt)
        admins = res.scalars().all()

        for admin in admins:
            if admin.id in top_5_admin_ids:
                admin.role = UserRoleEnum.ADMIN_A
            else:
                admin.role = UserRoleEnum.ADMIN_B

        # 2. Demotion Check: Admins who earned < 70 raw reps and lack active exemption -> demoted to USER
        for admin in admins:
            # Check exemption
            if admin.exempt_from_quota_until and admin.exempt_from_quota_until > now:
                continue
            
            if admin.rep_balance < 70.0:
                admin.role = UserRoleEnum.USER
                logging.info(f"Demoted admin {admin.id} to USER due to quota failure (<70 Rep).")

        # 3. Award Top-7 weekly message leaders (+50 Rep each)
        top_users = await user_repo.get_top_weekly_message_users(limit=7)
        for user_id, msgs in top_users:
            await user_repo.add_rep(user_id, 50.0)

        # 4. Reset weekly counters
        await user_repo.reset_weekly_counters()

        await session.commit()
    logging.info("Weekly Reset job completed successfully.")
