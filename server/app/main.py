from dotenv import load_dotenv, find_dotenv

# Automatically locate and load the server/.env file
load_dotenv(find_dotenv())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agent.loop import run_agentic_loop
app = FastAPI(title="InsightOut API")

# Allow Vite React Dev Server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: list[dict]

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        reply = run_agentic_loop(request.messages)
        return reply
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)