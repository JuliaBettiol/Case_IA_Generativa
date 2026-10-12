from unittest.mock import AsyncMock

import pytest

from app.llm.schemas import (
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)
from app.services.chat_service import ChatService


def resposta_llm(
    content=None,
    tool_calls=None,
    tokens=10,
):
    return LLMResponse(
        message=LLMMessage(
            content=content,
            tool_calls=tool_calls or [],
        ),
        usage=LLMUsage(
            prompt_tokens=tokens,
            completion_tokens=5,
            total_tokens=tokens + 5,
        ),
    )


@pytest.mark.asyncio
async def test_resposta_sem_ferramentas():
    service = ChatService()

    service.provider.chat = AsyncMock(
        return_value=resposta_llm(
            content="Olá! Como posso ajudar?"
        )
    )

    resultado = await service.responder(
        [{"role": "user", "content": "Olá"}]
    )

    assert resultado["content"] == "Olá! Como posso ajudar?"
    assert resultado["tool_calls"] == []
    assert resultado["usage"]["total_tokens"] == 15


@pytest.mark.asyncio
async def test_execucao_ferramenta(monkeypatch):
    service = ChatService()

    chamada = LLMToolCall(
        id="call_123",
        name="buscar_filiais",
        arguments='{"localidade": "LONDRINA"}',
    )

    service.provider.chat = AsyncMock(
        side_effect=[
            resposta_llm(tool_calls=[chamada]),
            resposta_llm(content="Encontrei uma filial."),
        ]
    )

    monkeypatch.setattr(
        "app.services.chat_service.executar_tool",
        lambda nome, argumentos: [{"codigo_filial": 1740}],
    )

    resultado = await service.responder(
        [
            {
                "role": "user",
                "content": "Quais filiais existem em Londrina?",
            }
        ]
    )

    assert resultado["content"] == "Encontrei uma filial."
    assert resultado["tool_calls"] == [
        {
            "name": "buscar_filiais",
            "arguments": {"localidade": "LONDRINA"},
        }
    ]

    assert resultado["usage"]["total_tokens"] == 30


@pytest.mark.asyncio
async def test_resultado_vazio_nao_repete_busca(monkeypatch):
    service = ChatService()

    chamada = LLMToolCall(
        id="call_123",
        name="buscar_filiais",
        arguments='{"localidade": "CIDADE_INEXISTENTE"}',
    )

    service.provider.chat = AsyncMock(
        side_effect=[
            resposta_llm(tool_calls=[chamada]),
            resposta_llm(
                content="Não encontrei filiais nessa localidade."
            ),
        ]
    )

    execucoes = []

    def fake_tool(nome, argumentos):
        execucoes.append((nome, argumentos))
        return []

    monkeypatch.setattr(
        "app.services.chat_service.executar_tool",
        fake_tool,
    )

    resultado = await service.responder(
        [
            {
                "role": "user",
                "content": "Existem filiais nessa cidade?",
            }
        ]
    )

    assert resultado["content"] == (
        "Não encontrei filiais nessa localidade."
    )
    assert len(execucoes) == 1

    segunda_chamada = service.provider.chat.call_args_list[1]
    assert segunda_chamada.kwargs["tools"] is None


@pytest.mark.asyncio
async def test_streaming_com_ferramenta(monkeypatch):
    service = ChatService()

    chamada = LLMToolCall(
        id="call_123",
        name="buscar_filiais",
        arguments='{"localidade": "LONDRINA"}',
    )

    service.provider.chat = AsyncMock(
        return_value=resposta_llm(tool_calls=[chamada])
    )

    monkeypatch.setattr(
        "app.services.chat_service.executar_tool",
        lambda nome, argumentos: [{"codigo_filial": 1740}],
    )

    async def fake_stream(messages):
        yield {
            "type": "content",
            "data": {"text": "Encontrei uma filial."},
        }
        yield {
            "type": "usage",
            "data": {
                "prompt_tokens": 20,
                "completion_tokens": 8,
                "total_tokens": 28,
            },
        }

    service.provider.stream_chat = fake_stream

    eventos = [
        evento
        async for evento in service.stream_resposta(
            [
                {
                    "role": "user",
                    "content": "Filiais em Londrina",
                }
            ]
        )
    ]

    assert eventos[0]["type"] == "metadata"
    assert eventos[1]["type"] == "content"
    assert eventos[1]["data"]["text"] == "Encontrei uma filial."

    usage = next(
        evento["data"]
        for evento in eventos
        if evento["type"] == "usage"
    )

    assert usage["total_tokens"] == 43


@pytest.mark.asyncio
async def test_streaming_resultado_vazio(monkeypatch):
    service = ChatService()

    chamada = LLMToolCall(
        id="call_123",
        name="buscar_filiais",
        arguments='{"localidade": "CIDADE_INEXISTENTE"}',
    )

    service.provider.chat = AsyncMock(
        side_effect=[
            resposta_llm(tool_calls=[chamada]),
            resposta_llm(
                content="Não encontrei filiais."
            ),
        ]
    )

    monkeypatch.setattr(
        "app.services.chat_service.executar_tool",
        lambda nome, argumentos: [],
    )

    eventos = [
        evento
        async for evento in service.stream_resposta(
            [
                {
                    "role": "user",
                    "content": "Filiais nessa cidade",
                }
            ]
        )
    ]

    textos = [
        evento["data"]["text"]
        for evento in eventos
        if evento["type"] == "content"
    ]

    assert textos == ["Não encontrei filiais."]

    assert service.provider.chat.await_count == 2


@pytest.mark.asyncio
async def test_streaming_sem_ferramentas():
    service = ChatService()

    service.provider.chat = AsyncMock(
        return_value=resposta_llm(
            content="Resposta direta."
        )
    )

    eventos = [
        evento
        async for evento in service.stream_resposta(
            [{"role": "user", "content": "Olá"}]
        )
    ]

    assert [evento["type"] for evento in eventos] == [
        "metadata",
        "content",
        "usage",
    ]