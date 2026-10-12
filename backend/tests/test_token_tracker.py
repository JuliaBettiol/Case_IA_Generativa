import asyncio

import pytest

from app.observability.token_tracker import (
    iniciar_contagem,
    registrar_tokens,
    obter_tokens,
    finalizar_contagem,
)


def test_acumula_tokens():
    token = iniciar_contagem()

    try:
        registrar_tokens(
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
        )

        registrar_tokens(
            prompt_tokens=50,
            completion_tokens=10,
            total_tokens=60,
        )

        assert obter_tokens() == {
            "prompt_tokens": 150,
            "completion_tokens": 30,
            "total_tokens": 180,
        }

    finally:
        finalizar_contagem(token)


def test_sem_consumo():
    token = iniciar_contagem()

    try:
        assert obter_tokens() is None

    finally:
        finalizar_contagem(token)


def test_contexto_finalizado():
    token = iniciar_contagem()

    try:
        registrar_tokens(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

        assert obter_tokens()["total_tokens"] == 15

    finally:
        finalizar_contagem(token)

    assert obter_tokens() is None


@pytest.mark.asyncio
async def test_contextos_independentes():
    async def executar(prompt_tokens):
        token = iniciar_contagem()

        try:
            registrar_tokens(
                prompt_tokens=prompt_tokens,
                completion_tokens=5,
                total_tokens=prompt_tokens + 5,
            )

            await asyncio.sleep(0)

            return obter_tokens()

        finally:
            finalizar_contagem(token)

    resultado_a, resultado_b = await asyncio.gather(
        executar(100),
        executar(200),
    )

    assert resultado_a["total_tokens"] == 105
    assert resultado_b["total_tokens"] == 205