from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from app.llm.schemas import LLMResponse

class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[dict[str, Any]]:
        pass