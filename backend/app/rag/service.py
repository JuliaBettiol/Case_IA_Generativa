from typing import Any
from app.llm.openai_provider import OpenAIProvider
from app.rag.retriever import Retriever

RAG_SYSTEM_PROMPT = """
Você é um assistente da Panvel especializado em responder perguntas
sobre medicamentos com base exclusivamente nas bulas fornecidas.

REGRAS:

1. Responda somente com informações presentes no contexto recuperado.

2. Não invente informações que não estejam nos trechos fornecidos.

3. Se o contexto não for suficiente para responder com segurança,
   diga claramente que não encontrou informação suficiente nas bulas
   disponíveis.

4. Não faça diagnóstico médico.

5. Não prescreva medicamentos, doses ou tratamentos individualizados.

6. Diferencie informações documentais da bula de orientação médica
   individual.

7. Quando houver riscos graves descritos no contexto, deixe claro que
   situações graves exigem avaliação profissional.

8. Ao final da resposta, inclua uma seção "Fonte" citando exatamente
   o nome do arquivo da bula fornecido no contexto.

9. Não cite uma fonte que não tenha sido fornecida no contexto.
"""


class RAGService:
    def __init__(self) -> None:
        self.retriever = Retriever()
        self.provider = OpenAIProvider()

    async def responder(
        self,
        pergunta: str,
    ) -> dict[str, Any]:
        documentos = await self.retriever.buscar(pergunta)

        if not documentos:
            return {
                "content": (
                    "Não encontrei informações suficientes "
                    "nas bulas disponíveis."
                ),
                "sources": [],
                "retrieved_documents": [],
                "usage": None,
            }

        contexto = "\n\n".join(
            (
                f"[Fonte: {documento['source']} | "
                f"Chunk: {documento['chunk_index']}]\n"
                f"{documento['text']}"
            )
            for documento in documentos
        )

        messages = [
            {
                "role": "system",
                "content": RAG_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"PERGUNTA:\n{pergunta}\n\n"
                    f"CONTEXTO DAS BULAS:\n{contexto}"
                ),
            },
        ]

        response = await self.provider.chat(
            messages=messages,
        )

        message = response.choices[0].message

        sources = list(
            dict.fromkeys(
                documento["source"]
                for documento in documentos
            )
        )

        return {
            "content": message.content,
            "sources": sources,
            "retrieved_documents": documentos,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            if response.usage
            else None,
        }