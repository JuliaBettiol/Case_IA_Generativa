import time

from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar


_timings: ContextVar[dict[str, float] | None] = ContextVar(
    "request_timings",
    default=None,
)


def iniciar_medicao():
    return _timings.set({})


def registrar_latencia(
    etapa: str,
    duracao_ms: float,
) -> None:
    atual = _timings.get()

    if atual is None:
        return

    atualizado = atual.copy()

    atualizado[etapa] = round(
        atualizado.get(etapa, 0.0) + duracao_ms,
        2,
    )

    _timings.set(atualizado)


def obter_latencias() -> dict[str, float]:
    atual = _timings.get()

    return atual.copy() if atual else {}


def finalizar_medicao(token) -> None:
    _timings.reset(token)


@contextmanager
def medir_etapa(etapa: str):
    inicio = time.perf_counter()

    try:
        yield
    finally:
        duracao_ms = (
            time.perf_counter() - inicio
        ) * 1000

        registrar_latencia(
            etapa,
            duracao_ms,
        )


@asynccontextmanager
async def medir_etapa_async(etapa: str):
    inicio = time.perf_counter()

    try:
        yield
    finally:
        duracao_ms = (
            time.perf_counter() - inicio
        ) * 1000

        registrar_latencia(
            etapa,
            duracao_ms,
        )