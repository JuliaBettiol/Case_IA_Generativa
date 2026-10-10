from typing import Any
from app.core.config import get_settings
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore

class Retriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embeddings = EmbeddingService()
        self.vector_store = VectorStore()

    async def buscar(
        self,
        pergunta: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        pergunta = pergunta.strip()

        if not pergunta:
            return []

        limite = top_k or self.settings.rag_top_k

        vetores = await self.embeddings.gerar_embeddings(
            [pergunta]
        )

        return self.vector_store.buscar(
            query_vector=vetores[0],
            limit=limite,
        )