import asyncio
from pathlib import Path
from app.core.config import get_settings
from app.rag.chunking import criar_chunks
from app.rag.embeddings import EmbeddingService
from app.rag.pdf_loader import carregar_bulas
from app.rag.vector_store import VectorStore

BATCH_SIZE = 50

settings = get_settings()
CORPUS_DIR = Path(settings.data_dir) / "corpus_bulas"


async def main() -> None:
    print("Carregando bulas...")

    documentos = carregar_bulas(CORPUS_DIR)
    print(f"Bulas encontradas: {len(documentos)}")

    chunks = criar_chunks(documentos)
    print(f"Chunks esperados: {len(chunks)}")

    vector_store = VectorStore()

    if vector_store.collection_esta_pronta(
        expected_points=len(chunks),
    ):
        print(
            "Índice já está pronto. "
            "Nenhuma reindexação necessária."
        )
        return

    print("Preparando coleção do Qdrant...")
    vector_store.recriar_collection()

    embedding_service = EmbeddingService()
    total = len(chunks)

    for inicio in range(0, total, BATCH_SIZE):
        fim = min(inicio + BATCH_SIZE, total)
        lote_chunks = chunks[inicio:fim]

        print(
            f"Gerando embeddings: "
            f"{inicio + 1}-{fim} de {total}"
        )

        embeddings = await embedding_service.gerar_embeddings(
            [chunk["text"] for chunk in lote_chunks]
        )

        vector_store.inserir_chunks(
            chunks=lote_chunks,
            embeddings=embeddings,
        )

    if not vector_store.collection_esta_pronta(
        expected_points=total,
    ):
        raise RuntimeError(
            "A indexação terminou, mas a coleção não contém "
            "a quantidade esperada de chunks."
        )

    print(f"Indexação concluída: {total} chunks.")


if __name__ == "__main__":
    asyncio.run(main())