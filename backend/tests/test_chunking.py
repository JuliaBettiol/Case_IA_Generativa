import pytest

from app.rag.chunking import criar_chunks


def test_documento_pequeno_gera_um_chunk():
    documentos = [
        {
            "text": "Texto curto de uma bula.",
            "source": "bula.pdf",
        }
    ]

    chunks = criar_chunks(
        documentos,
        tamanho=100,
        sobreposicao=10,
    )

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Texto curto de uma bula."
    assert chunks[0]["source"] == "bula.pdf"
    assert chunks[0]["chunk_index"] == 0


def test_chunks_preservam_source_e_indices():
    documentos = [
        {
            "text": "A" * 250,
            "source": "teste.pdf",
        }
    ]

    chunks = criar_chunks(
        documentos,
        tamanho=100,
        sobreposicao=20,
    )

    assert len(chunks) > 1

    assert all(
        chunk["source"] == "teste.pdf"
        for chunk in chunks
    )

    assert [
        chunk["chunk_index"]
        for chunk in chunks
    ] == list(range(len(chunks)))


@pytest.mark.parametrize(
    ("tamanho", "sobreposicao"),
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 101),
    ],
)
def test_parametros_invalidos(
    tamanho,
    sobreposicao,
):
    documentos = [
        {
            "text": "Teste",
            "source": "teste.pdf",
        }
    ]

    with pytest.raises(ValueError):
        criar_chunks(
            documentos,
            tamanho=tamanho,
            sobreposicao=sobreposicao,
        )