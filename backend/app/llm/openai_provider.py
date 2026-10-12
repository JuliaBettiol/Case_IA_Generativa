from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.schemas import (
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)
from app.observability.token_tracker import registrar_tokens


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
    ) -> LLMResponse:
        """
        Executa uma chamada ao modelo sem streaming.

        Converte a resposta específica da OpenAI para
        o contrato interno LLMResponse.

        Registra automaticamente o consumo de tokens
        no contexto da requisição.
        """

        request: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(
            **request
        )

        message = response.choices[0].message

        tool_calls = [
            LLMToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            )
            for tool_call in (message.tool_calls or [])
        ]

        usage = None

        if response.usage:
            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

            registrar_tokens(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )

        return LLMResponse(
            message=LLMMessage(
                content=message.content,
                tool_calls=tool_calls,
            ),
            usage=usage,
        )

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Executa uma chamada ao modelo com streaming.

        Envia eventos de conteúdo conforme o modelo
        produz a resposta.

        Registra o consumo de tokens quando a OpenAI
        disponibiliza os dados de uso.
        """

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            stream_options={
                "include_usage": True,
            },
        )

        async for chunk in stream:

            # Registra o consumo de tokens da geração.
            if chunk.usage:
                usage = LLMUsage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                )

                registrar_tokens(
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                )

                yield {
                    "type": "usage",
                    "data": usage.to_dict(),
                }

            # Alguns chunks contêm apenas metadados de uso.
            if not chunk.choices:
                continue

            # Recupera o texto produzido neste chunk.
            content = chunk.choices[0].delta.content

            if content:
                yield {
                    "type": "content",
                    "data": {
                        "text": content,
                    },
                }