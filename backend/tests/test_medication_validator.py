import pytest
from app.llm.schemas import LLMMessage, LLMResponse
from app.rag.medication_validator import MedicationValidator


def resposta_llm(texto: str) -> LLMResponse:
    return LLMResponse(
        message=LLMMessage(
            content=texto,
        )
    )


@pytest.mark.asyncio
async def test_medicamento_conhecido_nao_chama_llm(
    monkeypatch,
):
    validator = MedicationValidator()

    async def fake_chat(*args, **kwargs):
        pytest.fail(
            "O LLM não deveria ser chamado para "
            "medicamento conhecido."
        )

    monkeypatch.setattr(
        validator.provider,
        "chat",
        fake_chat,
    )

    resultado = await validator.validar(
        "Quais são os efeitos adversos do Rohydorm?"
    )

    assert resultado == "medicamento_disponivel"


@pytest.mark.asyncio
async def test_medicamento_fora_do_corpus(
    monkeypatch,
):
    validator = MedicationValidator()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("medicamento_especifico")

    monkeypatch.setattr(
        validator.provider,
        "chat",
        fake_chat,
    )

    resultado = await validator.validar(
        "Quais são os efeitos adversos da amoxicilina?"
    )

    assert resultado == "medicamento_indisponivel"


@pytest.mark.asyncio
async def test_consulta_geral_bulas(
    monkeypatch,
):
    validator = MedicationValidator()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("consulta_geral_bulas")

    monkeypatch.setattr(
        validator.provider,
        "chat",
        fake_chat,
    )

    resultado = await validator.validar(
        "Quais medicamentos das bulas podem causar sonolência?"
    )

    assert resultado == "consulta_geral_bulas"


@pytest.mark.asyncio
async def test_orientacao_individual(
    monkeypatch,
):
    validator = MedicationValidator()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("orientacao_individual")

    monkeypatch.setattr(
        validator.provider,
        "chat",
        fake_chat,
    )

    resultado = await validator.validar(
        "Qual medicamento devo tomar para dor no peito?"
    )

    assert resultado == "orientacao_individual"


@pytest.mark.asyncio
async def test_classificacao_invalida(
    monkeypatch,
):
    validator = MedicationValidator()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("categoria_inventada")

    monkeypatch.setattr(
        validator.provider,
        "chat",
        fake_chat,
    )

    with pytest.raises(
        ValueError,
        match="Classificação inválida",
    ):
        await validator.validar(
            "Pergunta não reconhecida"
        )