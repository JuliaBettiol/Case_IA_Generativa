from typing import Any
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.llm.base import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

        self.model = settings.openai_chat_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        request: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        return await self.client.chat.completions.create(**request)

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
    ):
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in stream:
            if chunk.usage:
                yield {
                    "type": "usage",
                    "data": {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    },
                }

            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                yield {
                    "type": "content",
                    "data": {
                        "text": content,
                    },
                }