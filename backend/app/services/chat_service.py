import json
from typing import Any
from app.core.config import get_settings
from app.llm.openai_provider import OpenAIProvider
from app.tools.definitions import TOOL_DEFINITIONS
from app.core.prompts import SYSTEM_PROMPT
from app.tools.registry import executar_tool

class ChatService:
    def __init__(self) -> None:
        self.provider = OpenAIProvider()
        self.settings = get_settings()

    async def responder(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        historico = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ]
        tools_executadas: list[dict[str, Any]] = []

        for _ in range(self.settings.max_tool_iterations):
            response = await self.provider.chat(
                messages=historico,
                tools=TOOL_DEFINITIONS,
            )

            message = response.choices[0].message

            if not message.tool_calls:
                return {
                    "content": message.content,
                    "tool_calls": tools_executadas,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None,
                }

            historico.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in message.tool_calls
                    ],
                }
            )

            for tool_call in message.tool_calls:
                nome = tool_call.function.name

                try:
                    argumentos = json.loads(
                        tool_call.function.arguments
                    )

                    resultado = executar_tool(
                        nome,
                        argumentos,
                    )

                    tools_executadas.append(
                        {
                            "name": nome,
                            "arguments": argumentos,
                        }
                    )

                    historico.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(
                                resultado,
                                ensure_ascii=False,
                            ),
                        }
                    )

                except Exception as exc:
                    historico.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(
                                {
                                    "error": str(exc),
                                },
                                ensure_ascii=False,
                            ),
                        }
                    )

        raise RuntimeError(
            "Limite máximo de iterações de ferramentas atingido."
        )