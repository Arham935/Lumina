import os, httpx
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE SETUP ---
DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DB_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- GROQ CONFIG ---
GROQ_KEY = os.getenv("GROQ_API_KEY")

@app.post("/v1/chat/completions")
async def chat(payload: dict, x_gateway_key: str = Header(None)):
    if not x_gateway_key:
        raise HTTPException(status_code=403, detail="Lumina Key Missing")

    async with AsyncSessionLocal() as session:
        try:
            # Check User in Supabase
            res = await session.execute(
                text("SELECT id, credit_balance FROM users WHERE api_key = :k"),
                {"k": x_gateway_key}
            )
            user = res.fetchone()
            
            if not user or user.credit_balance <= 0:
                raise HTTPException(status_code=402, detail="Low Balance or Invalid Key")

            # AI Call (Groq - FREE)
            async with httpx.AsyncClient() as client:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {GROQ_KEY}"}
                payload["model"] = "llama3-8b-8192"
                
                ai_resp = await client.post(url, headers=headers, json=payload, timeout=20.0)
                
                if ai_resp.status_code == 200:
                    # Deduct 1 Credit
                    await session.execute(
                        text("UPDATE users SET credit_balance = credit_balance - 1 WHERE id = :u"),
                        {"u": user.id}
                    )
                    await session.commit()
                    return ai_resp.json()
                else:
                    return {"error": "AI Provider Error", "details": ai_resp.text}

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"status": "Lumina is Alive", "founder": "Arham", "age": 14}
