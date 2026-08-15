from __future__ import annotations

import uuid

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app import __version__
from app.config import settings
from app.engine import reply_for
from app.models import ChatRequest, ChatResponse

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title=settings.app_name, version=__version__)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "name": settings.app_name,
        "version": __version__,
        "llm": bool(settings.llm_api_key),
    }


@app.get("/api/capabilities")
def capabilities() -> dict:
    return {
        "intents": [
            "greeting",
            "math",
            "convert",
            "time",
            "interview",
            "study",
            "notes",
            "privacy",
            "wellbeing",
        ],
        "llm_optional": True,
        "client_engine": True,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    session_id = body.session_id or str(uuid.uuid4())
    history = [m.model_dump() for m in body.history]
    result = reply_for(body.message, session_id=session_id, history=history)

    if settings.llm_api_key and result.intent == "unknown":
        llm_text = await _llm_reply(body.message, history)
        if llm_text:
            return ChatResponse(
                reply=llm_text,
                intent="llm",
                source="llm",
                suggestions=result.suggestions,
                session_id=session_id,
            )

    return ChatResponse(
        reply=result.reply,
        intent=result.intent,
        source=result.source,  # type: ignore[arg-type]
        suggestions=result.suggestions,
        session_id=session_id,
    )


async def _llm_reply(message: str, history: list[dict]) -> str | None:
    messages = [
        {
            "role": "system",
            "content": (
                "You are Lumen, a concise, warm assistant. Prefer short paragraphs. "
                "If the user may be in crisis, encourage real-world help and 988 in the US."
            ),
        }
    ]
    for item in history[-12:]:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": message})
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={"model": settings.llm_model, "messages": messages, "temperature": 0.4},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None


if ROOT.joinpath("assets").is_dir():
    app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "index.html")
