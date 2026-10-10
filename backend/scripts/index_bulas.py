import asyncio
from pathlib import Path
from app.rag.chunking import criar_chunks
from app.rag.embeddings import EmbeddingService
from app.rag.pdf_loader import carregar_bulas
from app.rag.vector_store import VectorStore

BATCH_SIZE = 50
from app.core.config import get_settings

settings = get_settings()

CORPUS_DIR = Path(settings.data_dir) / "corpus_bulas"

async def main() -> None:
    print("Carregando bulas...")

    documentos = carregar_bulas(CORPUS_DIR)

    print(f"Bulas encontradas: {len(documentos)}")

    chunks = criar_chunks(documentos)

    print(f"Chunks criados: {len(chunks)}")

    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    vector_store.recriar_collection()

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

    print("Indexação concluída.")

if __name__ == "__main__":
    asyncio.run(main())