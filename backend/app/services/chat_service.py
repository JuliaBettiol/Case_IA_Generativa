import json
from typing import Any, AsyncIterator

from app.core.config import get_settings
from app.core.prompts import SYSTEM_PROMPT
from app.llm.openai_provider import OpenAIProvider
from app.llm.schemas import LLMUsage
from app.tools.definitions import TOOL_DEFINITIONS
from app.tools.registry import executar_tool


class ChatService:
    def __init__(self) -> None:
        self.provider = OpenAIProvider()
        self.settings = get_settings()

    @staticmethod
    def _criar_historico(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ]

    @staticmethod
    def _mensagem_tool_calls(
        message: Any,
    ) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                    },
                }
                for tool_call in message.tool_calls
            ],
        }

    @staticmethod
    def _mensagem_resultado_tool(
        tool_call_id: str,
        resultado: Any,
    ) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(
                resultado,
                ensure_ascii=False,
                default=str,
            ),
        }

    @staticmethod
    def _somar_usage(
        total: dict[str, int],
        usage: LLMUsage | None,
    ) -> None:
        if usage is None:
            return

        total["prompt_tokens"] += usage.prompt_tokens
        total["completion_tokens"] += usage.completion_tokens
        total["total_tokens"] += usage.total_tokens

    @staticmethod
    def _usage_final(
        total: dict[str, int],
    ) -> dict[str, int] | None:
        if total["total_tokens"] == 0:
            return None

        return total

    async def responder(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        historico = self._criar_historico(messages)

        tools_executadas: list[dict[str, Any]] = []
        finalizar_sem_tools = False

        usage_total = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        for _ in range(self.settings.max_tool_iterations):
            response = await self.provider.chat(
                messages=historico,
                tools=(
                    None
                    if finalizar_sem_tools
                    else TOOL_DEFINITIONS
                ),
            )

            self._somar_usage(
                usage_total,
                response.usage,
            )

            message = response.message

            if not message.tool_calls:
                return {
                    "content": message.content or "",
                    "tool_calls": tools_executadas,
                    "usage": self._usage_final(
                        usage_total
                    ),
                }

            historico.append(
                self._mensagem_tool_calls(message)
            )

            houve_execucao_valida = False

            for tool_call in message.tool_calls:
                nome = tool_call.name

                try:
                    argumentos = json.loads(
                        tool_call.arguments
                    )

                    if not isinstance(argumentos, dict):
                        raise ValueError(
                            "Os argumentos da ferramenta "
                            "devem ser um objeto JSON."
                        )

                    chamada_repetida = any(
                        chamada["name"] == nome
                        and chamada["arguments"] == argumentos
                        for chamada in tools_executadas
                    )

                    if chamada_repetida:
                        resultado = {
                            "error": (
                                "Esta ferramenta já foi executada "
                                "com os mesmos argumentos neste turno. "
                                "Utilize o resultado anterior."
                            )
                        }

                    else:
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

                except Exception as exc:
                    resultado = {
                        "error": str(exc),
                    }

                historico.append(
                    self._mensagem_resultado_tool(
                        tool_call.id,
                        resultado,
                    )
                )

            if houve_execucao_valida:
                finalizar_sem_tools = True

        raise RuntimeError(
            "Limite máximo de iterações "
            "de ferramentas atingido."
        )

    async def stream_resposta(
        self,
        messages: list[dict[str, Any]],
    ) -> AsyncIterator[dict[str, Any]]:
        historico = self._criar_historico(messages)

        tools_executadas: list[dict[str, Any]] = []
        finalizar_sem_tools = False

        usage_total = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        for _ in range(self.settings.max_tool_iterations):
            response = await self.provider.chat(
                messages=historico,
                tools=(
                    None
                    if finalizar_sem_tools
                    else TOOL_DEFINITIONS
                ),
            )

            self._somar_usage(
                usage_total,
                response.usage,
            )

            message = response.message

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

                usage = self._usage_final(
                    usage_total
                )

                if usage:
                    yield {
                        "type": "usage",
                        "data": usage,
                    }

                return

            historico.append(
                self._mensagem_tool_calls(message)
            )

            houve_execucao_valida = False
            encontrou_resultado = False

            for tool_call in message.tool_calls:
                nome = tool_call.name

                try:
                    argumentos = json.loads(
                        tool_call.arguments
                    )

                    if not isinstance(argumentos, dict):
                        raise ValueError(
                            "Os argumentos da ferramenta "
                            "devem ser um objeto JSON."
                        )

                    chamada_repetida = any(
                        chamada["name"] == nome
                        and chamada["arguments"] == argumentos
                        for chamada in tools_executadas
                    )

                    if chamada_repetida:
                        resultado = {
                            "error": (
                                "Esta ferramenta já foi executada "
                                "com os mesmos argumentos neste turno. "
                                "Utilize o resultado anterior."
                            )
                        }

                    else:
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

                        if resultado:
                            encontrou_resultado = True

                except Exception as exc:
                    resultado = {
                        "error": str(exc),
                    }

                historico.append(
                    self._mensagem_resultado_tool(
                        tool_call.id,
                        resultado,
                    )
                )

            if houve_execucao_valida:
                finalizar_sem_tools = True

            if encontrou_resultado:
                yield {
                    "type": "metadata",
                    "data": {
                        "tool_calls": tools_executadas,
                    },
                }

                async for evento in self.provider.stream_chat(
                    historico
                ):
                    if evento["type"] == "usage":
                        dados = evento["data"]

                        usage_total["prompt_tokens"] += (
                            dados.get("prompt_tokens", 0)
                        )

                        usage_total["completion_tokens"] += (
                            dados.get("completion_tokens", 0)
                        )

                        usage_total["total_tokens"] += (
                            dados.get("total_tokens", 0)
                        )

                    else:
                        yield evento

                usage = self._usage_final(
                    usage_total
                )

                if usage:
                    yield {
                        "type": "usage",
                        "data": usage,
                    }

                return

            if houve_execucao_valida and finalizar_sem_tools:
                final_response = await self.provider.chat(
                    messages=historico,
                    tools=None,
                )

                self._somar_usage(
                    usage_total,
                    final_response.usage,
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
                        "text": (
                            final_response.message.content
                            or ""
                        ),
                    },
                }

                usage = self._usage_final(
                    usage_total
                )

                if usage:
                    yield {
                        "type": "usage",
                        "data": usage,
                    }

                return

        raise RuntimeError(
            "Limite máximo de iterações "
            "de ferramentas atingido."
        )