import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, ChatMemberUpdated
from redis.asyncio import Redis

class AntiRaidMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, window_seconds: int = 180, max_joins: int = 10):
        super().__init__()
        self.redis = redis
        self.window_seconds = window_seconds
        self.max_joins = max_joins

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, ChatMemberUpdated):
            # Check if event is user joining chat
            old_state = event.old_chat_member.status
            new_state = event.new_chat_member.status

            if old_state in ["left", "kicked"] and new_state in ["member", "administrator"]:
                chat_id = event.chat.id
                user_id = event.new_chat_member.user.id
                key = f"raid:{chat_id}"
                now = time.time()

                pipe = self.redis.pipeline()
                pipe.zadd(key, {str(user_id): now})
                pipe.zremrangebyscore(key, 0, now - self.window_seconds)
                pipe.zrange(key, 0, -1)
                pipe.expire(key, self.window_seconds)
                _, _, joined_users, _ = await pipe.execute()

                if len(joined_users) > self.max_joins:
                    # Lock down chat: ban raid members
                    bot = data["bot"]
                    for raider_id_bytes in joined_users:
                        try:
                            raider_id = int(raider_id_bytes.decode())
                            await bot.ban_chat_member(chat_id=chat_id, user_id=raider_id)
                        except Exception:
                            pass
                    
                    # Notify chat
                    try:
                        await bot.send_message(
                            chat_id=chat_id,
                            text="🚨 <b>ОБНАРУЖЕН РЕЙД!</b> Включен режим защиты! Все новые участники заблокированы."
                        )
                    except Exception:
                        pass
                    return

        return await handler(event, data)
