import pytest
from app.llm.schemas import LLMMessage, LLMResponse
from app.services.assistant_service import AssistantService
from app.services.router_service import RouterService


def resposta_llm(texto: str) -> LLMResponse:
    return LLMResponse(
        message=LLMMessage(
            content=texto,
        )
    )


@pytest.mark.asyncio
async def test_router_filiais(monkeypatch):
    router = RouterService()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("filiais")

    monkeypatch.setattr(
        router.provider,
        "chat",
        fake_chat,
    )

    resultado = await router.classificar(
        "Quais filiais possuem estacionamento?"
    )

    assert resultado == "filiais"


@pytest.mark.asyncio
async def test_router_bulas(monkeypatch):
    router = RouterService()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("bulas")

    monkeypatch.setattr(
        router.provider,
        "chat",
        fake_chat,
    )

    resultado = await router.classificar(
        "Quais os efeitos adversos do Rohydorm?"
    )

    assert resultado == "bulas"


@pytest.mark.asyncio
async def test_router_rejeita_resposta_invalida(
    monkeypatch,
):
    router = RouterService()

    async def fake_chat(*args, **kwargs):
        return resposta_llm("outra_rota")

    monkeypatch.setattr(
        router.provider,
        "chat",
        fake_chat,
    )

    with pytest.raises(
        ValueError,
        match="Rota inválida",
    ):
        await router.classificar("Pergunta qualquer")


@pytest.mark.asyncio
async def test_assistant_exige_mensagem():
    service = AssistantService()

    with pytest.raises(
        ValueError,
        match="pelo menos uma mensagem",
    ):
        await service.responder([])


@pytest.mark.asyncio
async def test_assistant_exige_usuario_por_ultimo():
    service = AssistantService()

    with pytest.raises(
        ValueError,
        match="última mensagem deve ser do usuário",
    ):
        await service.responder(
            [
                {
                    "role": "assistant",
                    "content": "Olá",
                }
            ]
        )