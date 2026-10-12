import pytest
from pydantic import ValidationError

from app.tools.registry import executar_tool


def test_buscar_filiais_londrina_com_estacionamento_e_clinic():
    resultado = executar_tool(
        "buscar_filiais",
        {
            "localidade": "LONDRINA",
            "estacionamento": "SIM",
            "panvel_clinic": "SIM",
        },
    )

    assert len(resultado) == 10

    for filial in resultado:
        assert filial["localidade"] == "LONDRINA"
        assert filial["estacionamento"] == "SIM"
        assert filial["panvel_clinic"] == "SIM"


def test_busca_e_case_insensitive():
    resultado = executar_tool(
        "buscar_filiais",
        {
            "localidade": "londrina",
            "estacionamento": "SIM",
        },
    )

    assert resultado
    assert all(
        filial["localidade"] == "LONDRINA"
        for filial in resultado
    )


def test_obter_filial_1740():
    resultado = executar_tool(
        "obter_filial",
        {"codigo_filial": "1740"},
    )

    assert resultado is not None
    assert str(resultado["codigo_filial"]) == "1740"
    assert resultado["localidade"] == "LONDRINA"
    assert resultado["panvel_clinic"] == "SIM"
    assert resultado["estacionamento"] == "SIM"
    assert resultado["atendimento_24_horas"] == "NÃO"


def test_obter_filial_inexistente():
    resultado = executar_tool(
        "obter_filial",
        {"codigo_filial": "999999"},
    )

    assert resultado is None


def test_tool_desconhecida():
    with pytest.raises(ValueError, match="Tool desconhecida"):
        executar_tool("tool_inexistente", {})


def test_valor_sim_nao_invalido():
    with pytest.raises(ValidationError):
        executar_tool(
            "buscar_filiais",
            {"estacionamento": "TALVEZ"},
        )