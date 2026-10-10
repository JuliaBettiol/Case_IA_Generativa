from typing import Literal

from app.llm.openai_provider import OpenAIProvider
from app.rag.medications import identificar_source


ValidationResult = Literal[
    "medicamento_disponivel",
    "medicamento_indisponivel",
    "sem_medicamento_especifico",
]


VALIDATION_PROMPT = """
Analise a pergunta do usuário.

Você deve identificar se a pergunta menciona explicitamente
um medicamento específico.

Responda SOMENTE com uma destas opções:

medicamento_especifico
sem_medicamento_especifico

Considere como medicamento específico tanto nomes comerciais
quanto princípios ativos.

Exemplos:

"Quais os efeitos adversos da amoxicilina?"
medicamento_especifico

"Para que serve o Rohydorm?"
medicamento_especifico

"Quais medicamentos podem causar sonolência?"
sem_medicamento_especifico

"Quais são os principais efeitos adversos descritos nas bulas?"
sem_medicamento_especifico
"""


class MedicationValidator:
    def __init__(self) -> None:
        self.provider = OpenAIProvider()

    async def validar(
        self,
        pergunta: str,
    ) -> ValidationResult:
        if identificar_source(pergunta):
            return "medicamento_disponivel"

        response = await self.provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": VALIDATION_PROMPT,
                },
                {
                    "role": "user",
                    "content": pergunta,
                },
            ],
        )

        resultado = (
            response.choices[0]
            .message.content
            .strip()
            .lower()
        )

        if resultado == "medicamento_especifico":
            return "medicamento_indisponivel"

        if resultado == "sem_medicamento_especifico":
            return "sem_medicamento_especifico"

        raise ValueError(
            "Classificação inválida retornada pelo "
            f"validador de medicamento: {resultado}"
        )