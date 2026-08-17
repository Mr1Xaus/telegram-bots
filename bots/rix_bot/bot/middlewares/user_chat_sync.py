from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from bot.database.session import AsyncSessionLocal
from bot.database.repositories.user_repo import UserRepo
from bot.services.economy_service import EconomyService

class UserChatSyncMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.from_user and not event.from_user.is_bot:
            async with AsyncSessionLocal() as session:
                user_repo = UserRepo(session)
                # Auto-register / update active timestamp
                await user_repo.get_or_create(event.from_user.id)
                await user_repo.update_last_active(event.from_user.id)

                # If message is in group/supergroup, track stats & process economy
                if event.chat and event.chat.type in ["group", "supergroup"]:
                    rewarded, earned = await EconomyService.process_message_reward(
                        user_repo=user_repo,
                        user_id=event.from_user.id,
                        chat_id=event.chat.id
                    )
                    if rewarded:
                        data["earned_rep_notice"] = earned
                await session.commit()

        return await handler(event, data)
