from fastapi import FastAPI, Depends, Header
from app.core.auth import verify_api_key
from app.core.limiter import apply_rate_limit
from app.services.proxy import proxy_service
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI(title="Zero-Budget-AI-Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/v1/chat/completions")
async def chat(
    payload: dict, 
    user_id: str = Depends(verify_api_key),
    x_user_openai_key: Optional[str] = Header(None) # User apni key yahan bhej sakta hai
):
    await apply_rate_limit(user_id)
    return await proxy_service.execute_request(user_id, payload, x_user_openai_key)

@app.get("/health")
async def health(): return {"status": "operational", "budget": "zero-cost"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)