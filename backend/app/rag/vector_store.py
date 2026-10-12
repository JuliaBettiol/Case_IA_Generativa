import uuid
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from app.core.config import get_settings

class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()

        self.client = QdrantClient(
            url=settings.qdrant_url,
        )

        self.collection_name = settings.qdrant_collection

    def collection_esta_pronta(
        self,
        expected_points: int,
    ) -> bool:
        if not self.client.collection_exists(
            collection_name=self.collection_name
        ):
            return False

        info = self.client.get_collection(
            collection_name=self.collection_name
        )

        return info.points_count == expected_points
    
    def criar_collection(
        self,
        vector_size: int = 1536,
    ) -> None:
        if self.client.collection_exists(
            collection_name=self.collection_name
        ):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def recriar_collection(
        self,
        vector_size: int = 1536,
    ) -> None:
        if self.client.collection_exists(
            collection_name=self.collection_name
        ):
            self.client.delete_collection(
                collection_name=self.collection_name
            )

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    @staticmethod
    def _gerar_id(
        source: str,
        chunk_index: int,
    ) -> str:
        chave = f"{source}:{chunk_index}"

        return str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                chave,
            )
        )

    def inserir_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Quantidade de chunks diferente da quantidade de embeddings."
            )

        pontos = [
            PointStruct(
                id=self._gerar_id(
                    source=chunk["source"],
                    chunk_index=chunk["chunk_index"],
                ),
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
            for chunk, embedding in zip(
                chunks,
                embeddings,
            )
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=pontos,
        )

    def buscar(
        self,
        query_vector: list[float],
        limit: int = 6,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        filtro = None

        if source:
            filtro = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source),
                    )
                ]
            )

        resultados = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=filtro,
            limit=limit,
            with_payload=True,
        ).points

        return [
            {
                "score": resultado.score,
                "text": resultado.payload.get("text"),
                "source": resultado.payload.get("source"),
                "chunk_index": resultado.payload.get("chunk_index"),
            }
            for resultado in resultados
        ]