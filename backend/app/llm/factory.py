from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.openai_provider import OpenAIProvider


def create_llm_provider() -> LLMProvider:
    """
    Cria o provedor LLM configurado.

    A escolha do provedor fica centralizada aqui,
    evitando dependências diretas nos serviços.
    """

    settings = get_settings()

    provider_name = settings.llm_provider.strip().lower()

    if provider_name == "openai":
        return OpenAIProvider()

    raise ValueError(
        f"Provedor LLM não suportado: {provider_name}. "
        "Provedores disponíveis: openai."
    )