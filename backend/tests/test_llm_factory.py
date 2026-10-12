from types import SimpleNamespace

import pytest

from app.llm import factory


def test_factory_cria_openai(monkeypatch):
    class FakeOpenAIProvider:
        pass

    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: SimpleNamespace(llm_provider="openai"),
    )

    monkeypatch.setattr(
        factory,
        "OpenAIProvider",
        FakeOpenAIProvider,
    )

    provider = factory.create_llm_provider()

    assert isinstance(provider, FakeOpenAIProvider)


def test_factory_aceita_nome_case_insensitive(monkeypatch):
    class FakeOpenAIProvider:
        pass

    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: SimpleNamespace(llm_provider=" OPENAI "),
    )

    monkeypatch.setattr(
        factory,
        "OpenAIProvider",
        FakeOpenAIProvider,
    )

    provider = factory.create_llm_provider()

    assert isinstance(provider, FakeOpenAIProvider)


def test_factory_rejeita_provider_desconhecido(monkeypatch):
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: SimpleNamespace(llm_provider="anthropic"),
    )

    with pytest.raises(
        ValueError,
        match="Provedor LLM não suportado",
    ):
        factory.create_llm_provider()