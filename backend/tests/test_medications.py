from app.rag.medications import (
    identificar_source,
    normalizar,
    source_existe,
)


def test_normalizar_remove_acentos_e_caixa():
    assert normalizar("  MEDICAÇÃO  ") == "medicacao"


def test_identificar_rohydorm():
    assert (
        identificar_source(
            "Quais são os efeitos adversos do Rohydorm?"
        )
        == "102622_rohydorm_flunitrazepam.pdf"
    )


def test_identificar_principio_ativo():
    assert (
        identificar_source(
            "Quais informações existem sobre flunitrazepam?"
        )
        == "102622_rohydorm_flunitrazepam.pdf"
    )


def test_medicamento_fora_do_corpus():
    assert identificar_source(
        "Quais são os efeitos da amoxicilina?"
    ) is None


def test_source_existe():
    assert source_existe(
        "102622_rohydorm_flunitrazepam.pdf"
    )


def test_source_inexistente():
    assert not source_existe(
        "amoxicilina.pdf"
    )