from unittest.mock import AsyncMock, MagicMock
import pytest
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore

@pytest.fixture
def retriever():
    service = Retriever()

    service.embeddings.gerar_embeddings = AsyncMock(
        return_value=[[0.1, 0.2, 0.3]]
    )

    service.vector_store.buscar = MagicMock(return_value=[])

    return service


@pytest.mark.asyncio
async def test_retriever_filtra_medicamento_conhecido(retriever):
    """Perguntas sobre Rohydorm devem filtrar a busca pela bula correta."""

    await retriever.buscar(
        "Quais são os efeitos adversos do Rohydorm?"
    )

    retriever.vector_store.buscar.assert_called_once_with(
        query_vector=[0.1, 0.2, 0.3],
        limit=retriever.settings.rag_top_k,
        source="102622_rohydorm_flunitrazepam.pdf",
    )


@pytest.mark.asyncio
async def test_retriever_consulta_geral_sem_filtro(retriever):
    """Consultas gerais devem pesquisar todas as bulas."""

    await retriever.buscar(
        "Quais medicamentos das bulas podem causar sonolência?"
    )

    retriever.vector_store.buscar.assert_called_once_with(
        query_vector=[0.1, 0.2, 0.3],
        limit=retriever.settings.rag_top_k,
        source=None,
    )


@pytest.mark.asyncio
async def test_retriever_aplica_threshold(retriever):
    """Documentos abaixo do threshold não devem ser retornados."""

    threshold = retriever.settings.rag_score_threshold

    retriever.vector_store.buscar.return_value = [
        {"source": "bula_a.pdf", "score": threshold + 0.1},
        {"source": "bula_b.pdf", "score": threshold - 0.1},
    ]

    resultado = await retriever.buscar(
        "Quais são os efeitos adversos?"
    )

    assert len(resultado) == 1
    assert resultado[0]["source"] == "bula_a.pdf"


@pytest.mark.asyncio
async def test_retriever_sem_threshold(retriever):
    """Consultas gerais podem desabilitar o filtro de relevância."""

    retriever.vector_store.buscar.return_value = [
        {"source": "bula_a.pdf", "score": 0.2},
        {"source": "bula_b.pdf", "score": 0.3},
    ]

    resultado = await retriever.buscar(
        "Quais medicamentos aparecem nas bulas?",
        aplicar_threshold=False,
    )

    assert len(resultado) == 2


@pytest.mark.asyncio
async def test_retriever_pergunta_vazia(retriever):
    """Perguntas vazias não devem gerar embeddings nem consultar o Qdrant."""

    resultado = await retriever.buscar("   ")

    assert resultado == []

    retriever.embeddings.gerar_embeddings.assert_not_called()
    retriever.vector_store.buscar.assert_not_called()


def test_vector_store_aplica_filtro_source():
    """O Qdrant deve receber o filtro antes de selecionar os chunks."""

    store = VectorStore()

    store.client.query_points = MagicMock(
        return_value=MagicMock(points=[])
    )

    store.buscar(
        query_vector=[0.1, 0.2, 0.3],
        limit=6,
        source="102622_rohydorm_flunitrazepam.pdf",
    )

    argumentos = store.client.query_points.call_args.kwargs

    filtro = argumentos["query_filter"]

    assert filtro is not None
    assert filtro.must[0].key == "source"
    assert (
        filtro.must[0].match.value
        == "102622_rohydorm_flunitrazepam.pdf"
    )

    assert argumentos["limit"] == 6


def test_vector_store_consulta_sem_filtro():
    """Consultas gerais não devem restringir a origem dos documentos."""

    store = VectorStore()

    store.client.query_points = MagicMock(
        return_value=MagicMock(points=[])
    )

    store.buscar(
        query_vector=[0.1, 0.2, 0.3],
        limit=6,
    )

    argumentos = store.client.query_points.call_args.kwargs

    assert argumentos["query_filter"] is None