from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[dict[str, Any]]:
        pass