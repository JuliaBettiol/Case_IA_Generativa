from typing import Literal

from app.llm.openai_provider import OpenAIProvider
from app.rag.medications import identificar_source


ValidationResult = Literal[
    "medicamento_disponivel",
    "medicamento_indisponivel",
    "consulta_geral_bulas",
    "orientacao_individual",
]


VALIDATION_PROMPT = """
Classifique a pergunta do usuário em exatamente uma destas categorias:

medicamento_especifico
consulta_geral_bulas
orientacao_individual

DEFINIÇÕES:

medicamento_especifico
- a pergunta menciona explicitamente um medicamento, nome comercial
  ou princípio ativo.

consulta_geral_bulas
- a pergunta pede informações gerais ou comparações sobre os
  medicamentos presentes nas bulas;
- não pede indicação personalizada de tratamento.

orientacao_individual
- o usuário pergunta qual medicamento deve tomar;
- pede indicação, prescrição, dose ou tratamento para si ou outra pessoa;
- descreve sintomas buscando uma recomendação individual de medicamento.

EXEMPLOS:

"Quais são os efeitos adversos da amoxicilina?"
medicamento_especifico

"Para que serve o Rohydorm?"
medicamento_especifico

"Quais medicamentos das bulas podem causar sonolência?"
consulta_geral_bulas

"Quais são os principais efeitos adversos descritos nas bulas?"
consulta_geral_bulas

"Qual medicamento devo tomar para dor no peito?"
orientacao_individual

"Estou com dor de cabeça. O que devo tomar?"
orientacao_individual

"Qual dose devo tomar para tratar minha dor?"
orientacao_individual

Responda SOMENTE com uma das três categorias.
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

        if resultado == "consulta_geral_bulas":
            return "consulta_geral_bulas"

        if resultado == "orientacao_individual":
            return "orientacao_individual"

        raise ValueError(
            "Classificação inválida retornada pelo "
            f"validador de medicamento: {resultado}"
        )