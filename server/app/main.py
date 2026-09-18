import logging

from app.agent.loop import ChatMessage, run_agentic_loop
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, ValidationError

logger = logging.getLogger(__name__)

# Automatically locate and load the server/.env file
load_dotenv(find_dotenv())

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
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatMessage]


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        return run_agentic_loop(request.messages)
    except (TypeError, ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail="Unable to process chat request") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)