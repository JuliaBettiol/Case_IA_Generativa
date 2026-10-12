import asyncio

import pytest

from app.observability.timing import (
    iniciar_medicao,
    registrar_latencia,
    obter_latencias,
    finalizar_medicao,
    medir_etapa,
    medir_etapa_async,
)


def test_registrar_latencia():
    token = iniciar_medicao()

    try:
        registrar_latencia("router_ms", 100.5)
        registrar_latencia("router_ms", 50.25)

        assert obter_latencias() == {
            "router_ms": 150.75
        }

    finally:
        finalizar_medicao(token)


def test_sem_medicoes():
    token = iniciar_medicao()

    try:
        assert obter_latencias() == {}

    finally:
        finalizar_medicao(token)


def test_medicao_sincrona():
    token = iniciar_medicao()

    try:
        with medir_etapa("vector_search_ms"):
            sum(range(1000))

        latencias = obter_latencias()

        assert "vector_search_ms" in latencias
        assert latencias["vector_search_ms"] >= 0

    finally:
        finalizar_medicao(token)


@pytest.mark.asyncio
async def test_medicao_assincrona():
    token = iniciar_medicao()

    try:
        async with medir_etapa_async("llm_generation_ms"):
            await asyncio.sleep(0.01)

        latencias = obter_latencias()

        assert "llm_generation_ms" in latencias
        assert latencias["llm_generation_ms"] >= 10

    finally:
        finalizar_medicao(token)


@pytest.mark.asyncio
async def test_contextos_independentes():
    async def executar(nome):
        token = iniciar_medicao()

        try:
            registrar_latencia(nome, 100)

            await asyncio.sleep(0)

            return obter_latencias()

        finally:
            finalizar_medicao(token)

    resultado_a, resultado_b = await asyncio.gather(
        executar("router_ms"),
        executar("embedding_ms"),
    )

    assert resultado_a == {"router_ms": 100}
    assert resultado_b == {"embedding_ms": 100}


def test_contexto_finalizado():
    token = iniciar_medicao()

    registrar_latencia("router_ms", 100)

    finalizar_medicao(token)

    assert obter_latencias() == {}