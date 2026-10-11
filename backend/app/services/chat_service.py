import json
from typing import Any

from app.core.config import get_settings
from app.core.prompts import SYSTEM_PROMPT
from app.llm.openai_provider import OpenAIProvider
from app.tools.definitions import TOOL_DEFINITIONS
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

        # Quando uma busca já retornar dados suficientes,
        # desabilitamos novas tools e deixamos o LLM apenas
        # formular a resposta final.
        finalizar_sem_tools = False

        for _ in range(self.settings.max_tool_iterations):
            response = await self.provider.chat(
                messages=historico,
                tools=(
                    None
                    if finalizar_sem_tools
                    else TOOL_DEFINITIONS
                ),
            )

            message = response.choices[0].message

            # Se o modelo não solicitou nenhuma ferramenta,
            # temos a resposta final.
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

            # Registra a solicitação de ferramentas feita pelo modelo.
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

                    # Uma busca de filiais que encontrou resultados
                    # já fornece dados suficientes para o LLM
                    # formular a resposta final.
                    #
                    # Na próxima iteração, nenhuma nova ferramenta
                    # será disponibilizada.
                    if (
                        nome == "buscar_filiais"
                        and resultado
                    ):
                        finalizar_sem_tools = True

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

    async def stream_resposta(
        self,
        messages: list[dict[str, Any]],
    ):
        historico = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ]

        tools_executadas: list[dict[str, Any]] = []
        finalizar_sem_tools = False

        for _ in range(
            self.settings.max_tool_iterations
        ):
            response = await self.provider.chat(
                messages=historico,
                tools=(
                    None
                    if finalizar_sem_tools
                    else TOOL_DEFINITIONS
                ),
            )

            message = response.choices[0].message

            # O modelo já produziu a resposta final sem precisar
            # solicitar uma ferramenta.
            if not message.tool_calls:
                yield {
                    "type": "metadata",
                    "data": {
                        "tool_calls": tools_executadas,
                    },
                }

                yield {
                    "type": "content",
                    "data": {
                        "text": message.content or "",
                    },
                }

                if response.usage:
                    yield {
                        "type": "usage",
                        "data": {
                            "prompt_tokens":
                                response.usage.prompt_tokens,
                            "completion_tokens":
                                response.usage.completion_tokens,
                            "total_tokens":
                                response.usage.total_tokens,
                        },
                    }

                return

            historico.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name":
                                    tool_call.function.name,
                                "arguments":
                                    tool_call.function.arguments,
                            },
                        }
                        for tool_call
                        in message.tool_calls
                    ],
                }
            )

            encontrou_resultado = False
            houve_execucao_valida = False

            for tool_call in message.tool_calls:
                nome = tool_call.function.name

                try:
                    argumentos = json.loads(
                        tool_call.function.arguments
                    )

                    # Evita executar exatamente a mesma ferramenta
                    # com os mesmos argumentos mais de uma vez no
                    # mesmo turno.
                    chamada_repetida = any(
                        chamada["name"] == nome
                        and chamada["arguments"] == argumentos
                        for chamada in tools_executadas
                    )

                    if chamada_repetida:
                        historico.append(
                            {
                                "role": "tool",
                                "tool_call_id":
                                    tool_call.id,
                                "content": json.dumps(
                                    {
                                        "error": (
                                            "Esta ferramenta já foi "
                                            "executada com estes mesmos "
                                            "argumentos neste turno. "
                                            "Use o resultado anterior."
                                        )
                                    },
                                    ensure_ascii=False,
                                ),
                            }
                        )
                        continue

                    resultado = executar_tool(
                        nome,
                        argumentos,
                    )

                    houve_execucao_valida = True

                    tools_executadas.append(
                        {
                            "name": nome,
                            "arguments": argumentos,
                        }
                    )

                    historico.append(
                        {
                            "role": "tool",
                            "tool_call_id":
                                tool_call.id,
                            "content": json.dumps(
                                resultado,
                                ensure_ascii=False,
                            ),
                        }
                    )

                    if resultado:
                        encontrou_resultado = True

                except Exception as exc:
                    historico.append(
                        {
                            "role": "tool",
                            "tool_call_id":
                                tool_call.id,
                            "content": json.dumps(
                                {
                                    "error": str(exc),
                                },
                                ensure_ascii=False,
                            ),
                        }
                    )

            # Depois de uma busca válida de filiais, não oferecemos
            # novas ferramentas na iteração seguinte. O modelo deve
            # apenas formular a resposta final com os dados obtidos.
            if houve_execucao_valida:
                finalizar_sem_tools = True

            if encontrou_resultado:
                yield {
                    "type": "metadata",
                    "data": {
                        "tool_calls": tools_executadas,
                    },
                }

                async for evento in (
                    self.provider.stream_chat(
                        historico
                    )
                ):
                    yield evento

                return

            # Resultado vazio também é uma resposta válida.
            # O modelo deve explicar que nenhuma filial corresponde
            # aos filtros, sem inventar novas buscas complementares.
            if houve_execucao_valida and finalizar_sem_tools:
                final_response = await self.provider.chat(
                    messages=historico,
                    tools=None,
                )

                final_message = (
                    final_response.choices[0].message
                )

                yield {
                    "type": "metadata",
                    "data": {
                        "tool_calls": tools_executadas,
                    },
                }

                yield {
                    "type": "content",
                    "data": {
                        "text": final_message.content or "",
                    },
                }

                if final_response.usage:
                    yield {
                        "type": "usage",
                        "data": {
                            "prompt_tokens":
                                final_response.usage.prompt_tokens,
                            "completion_tokens":
                                final_response.usage.completion_tokens,
                            "total_tokens":
                                final_response.usage.total_tokens,
                        },
                    }

                return

        raise RuntimeError(
            "Limite máximo de iterações "
            "de ferramentas atingido."
        )