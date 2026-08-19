import time
from app.db.redis import redis_client
from fastapi import HTTPException

async def apply_rate_limit(user_id: str):
    now = time.time()
    key = f"limit:{user_id}"
    async with redis_client.pipeline(transaction=True) as pipe:
        await pipe.zremrangebyscore(key, 0, now - 60)
        await pipe.zadd(key, {str(now): now})
        await pipe.zcard(key)
        res = await pipe.execute()
    if res[2] > 50: raise HTTPException(status_code=429, detail="Too many requests")