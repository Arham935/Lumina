import httpx
from app.config import settings
from app.db.postgres import AsyncSessionLocal
from sqlalchemy import text

class ProxyService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def execute_request(self, user_id: str, payload: dict, user_provided_key: str = None):
        # BUDGET LOGIC:
        # Agar user ne apni key di hai -> Use OpenAI (User ka kharcha)
        # Agar user ne key nahi di -> Use Groq (Aapka Free system)
        
        if user_provided_key:
            url = "https://api.openai.com/v1/chat/completions"
            key = user_provided_key
            print(f"DEBUG: Using User Key for {user_id}")
        else:
            url = "https://api.groq.com/openai/v1/chat/completions"
            key = settings.GROQ_API_KEY
            payload["model"] = "llama3-8b-8192" # Free model
            print(f"DEBUG: Using Free Groq for {user_id}")
            
        try:
            resp = await self.client.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            data = resp.json()
            
            # Billing tracking (Aapke database mein record rahega)
            tokens = data.get("usage", {}).get("total_tokens", 0)
            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("UPDATE users SET credit_balance = credit_balance - 1 WHERE id = :u"),
                    {"u": user_id}
                )
                await session.commit()
            return data
        except Exception as e:
            return {"error": "AI Provider down", "details": str(e)}

proxy_service = ProxyService()