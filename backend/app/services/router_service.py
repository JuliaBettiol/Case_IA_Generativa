from typing import Literal
from app.llm.openai_provider import OpenAIProvider

Route = Literal["filiais", "bulas"]

ROUTER_PROMPT = """
Classifique a pergunta do usuário em exatamente uma das categorias:

filiais
- perguntas sobre lojas ou filiais da Panvel
- localização de filiais
- serviços disponíveis em filiais
- estacionamento
- delivery
- Panvel Clinic
- atendimento 24 horas
- características de uma filial

bulas
- perguntas sobre medicamentos
- efeitos adversos
- contraindicações
- composição
- interações medicamentosas
- modo de uso
- informações farmacológicas
- dúvidas que devem ser respondidas usando bulas

Responda SOMENTE com uma palavra:

filiais

ou

bulas
"""

class RouterService:
    def __init__(self) -> None:
        self.provider = OpenAIProvider()

    async def classificar(
        self,
        pergunta: str,
    ) -> Route:
        response = await self.provider.chat(
            messages=[
                {
                    "role": "system",
                    "content": ROUTER_PROMPT,
                },
                {
                    "role": "user",
                    "content": pergunta,
                },
            ],
        )

        rota = (
            response.choices[0]
            .message.content
            .strip()
            .lower()
        )

        if rota == "filiais":
            return "filiais"

        if rota == "bulas":
            return "bulas"

        raise ValueError(
            f"Rota inválida retornada pelo modelo: {rota}"
        )