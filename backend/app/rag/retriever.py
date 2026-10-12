from typing import Any

from app.core.config import get_settings
from app.rag.embeddings import EmbeddingService
from app.rag.medications import identificar_source
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
        aplicar_threshold: bool = True,
    ) -> list[dict[str, Any]]:
        pergunta = pergunta.strip()

        if not pergunta:
            return []

        limite = top_k or self.settings.rag_top_k
        source_esperada = identificar_source(pergunta)

        vetores = await self.embeddings.gerar_embeddings(
            [pergunta]
        )

        resultados = self.vector_store.buscar(
            query_vector=vetores[0],
            limit=limite,
            source=source_esperada,
        )

        if aplicar_threshold:
            resultados = [
                documento
                for documento in resultados
                if documento.get("score", 0)
                >= self.settings.rag_score_threshold
            ]

        return resultados