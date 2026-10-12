from contextvars import ContextVar
from typing import Any


_token_usage: ContextVar[dict[str, int] | None] = ContextVar(
    "token_usage",
    default=None,
)


def iniciar_contagem():
    return _token_usage.set(
        {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    )


def registrar_tokens(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
) -> None:
    atual = _token_usage.get()

    if atual is None:
        return

    # Criamos um novo dicionário para evitar mutações
    # compartilhadas entre contextos assíncronos.
    atualizado = {
        "prompt_tokens": (
            atual["prompt_tokens"] + prompt_tokens
        ),
        "completion_tokens": (
            atual["completion_tokens"] + completion_tokens
        ),
        "total_tokens": (
            atual["total_tokens"] + total_tokens
        ),
    }

    _token_usage.set(atualizado)


def obter_tokens() -> dict[str, int] | None:
    atual = _token_usage.get()

    if atual is None:
        return None

    if atual["total_tokens"] == 0:
        return None

    return atual.copy()


def finalizar_contagem(token: Any) -> None:
    _token_usage.reset(token)