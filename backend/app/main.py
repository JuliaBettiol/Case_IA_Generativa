from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Panvel AI Assistant",
    description="API do assistente de IA Generativa para o Grupo Panvel",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "panvel-ai-assistant",
    }