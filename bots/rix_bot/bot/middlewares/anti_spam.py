import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from redis.asyncio import Redis

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, limit: int = 5, period: int = 3):
        super().__init__()
        self.redis = redis
        self.limit = limit
        self.period = period

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.from_user and not event.from_user.is_bot:
            user_id = event.from_user.id
            key = f"antispam:{user_id}"
            
            now = time.time()
            pipe = self.redis.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.zremrangebyscore(key, 0, now - self.period)
            pipe.zcard(key)
            pipe.expire(key, self.period)
            _, _, count, _ = await pipe.execute()

            if count > self.limit:
                # Delete offender message silently
                try:
                    await event.delete()
                except Exception:
                    pass
                return  # Block handler execution

        return await handler(event, data)
