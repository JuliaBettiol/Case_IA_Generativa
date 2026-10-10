from openai import AsyncOpenAI
from app.core.config import get_settings

class EmbeddingService:
    def __init__(self) -> None:
        settings = get_settings()

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

        self.model = settings.openai_embedding_model

    async def gerar_embeddings(
        self,
        textos: list[str],
    ) -> list[list[float]]:
        if not textos:
            return []

        response = await self.client.embeddings.create(
            model=self.model,
            input=textos,
        )

        return [
            item.embedding
            for item in response.data
        ]