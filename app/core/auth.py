from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from app.db.redis import redis_client
from app.db.postgres import AsyncSessionLocal
from sqlalchemy import text

API_KEY_HEADER = APIKeyHeader(name="X-Gateway-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    cache_key = f"auth:{api_key}"
    uid = await redis_client.get(cache_key)
    if uid: return uid
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id FROM users WHERE api_key = :k"), {"k": api_key})
        user = res.fetchone()
        if not user: raise HTTPException(status_code=403, detail="Invalid Key")
        await redis_client.setex(cache_key, 600, str(user.id))
        return str(user.id)