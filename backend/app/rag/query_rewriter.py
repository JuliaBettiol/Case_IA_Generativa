from typing import Any

from app.llm.openai_provider import OpenAIProvider


QUERY_REWRITER_PROMPT = """
Sua tarefa é transformar a ÚLTIMA pergunta do usuário em uma pergunta
independente, usando as mensagens anteriores somente para resolver
referências que dependam do contexto.

REGRAS:

1. Preserve rigorosamente a intenção da última pergunta.

2. Nunca troque o assunto solicitado. Por exemplo:
   - indicação não deve virar efeitos adversos;
   - efeitos adversos não devem virar contraindicações;
   - contraindicações não devem virar modo de uso.

3. Preserve o medicamento mencionado anteriormente quando a última
   pergunta fizer referência implícita a ele.

4. Resolva expressões como "ele", "esse medicamento", "dele",
   "e os efeitos adversos?", "e as contraindicações?" e semelhantes.

5. Não responda à pergunta.

6. Não acrescente informações médicas.

7. Não invente nomes de medicamentos.

8. Retorne somente a pergunta reescrita.
"""


class QueryRewriter:
    def __init__(self) -> None:
        self.provider = OpenAIProvider()

    async def reescrever(
        self,
        messages: list[dict[str, Any]],
    ) -> str:
        if not messages:
            raise ValueError(
                "É necessário fornecer o histórico da conversa."
            )

        ultima_pergunta = messages[-1].get(
            "content",
            "",
        ).strip()

        if not ultima_pergunta:
            raise ValueError(
                "A última mensagem não possui conteúdo."
            )

        # No primeiro turno não existe contexto anterior
        # para resolver. Preservamos exatamente a pergunta.
        if len(messages) == 1:
            return ultima_pergunta

        response = await self.provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": QUERY_REWRITER_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "HISTÓRICO DA CONVERSA:\n"
                        f"{self._formatar_historico(messages)}"
                        "\n\n"
                        "Reescreva somente a última pergunta."
                    ),
                },
            ],
        )

        return (response.message.content or "").strip()

    @staticmethod
    def _formatar_historico(
        messages: list[dict[str, Any]],
    ) -> str:
        linhas = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            linhas.append(
                f"{role}: {content}"
            )

        return "\n".join(linhas)